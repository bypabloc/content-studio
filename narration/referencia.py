"""Medición, normalización y verificación de una referencia de voz. Solo stdlib + ffmpeg.

Lo usan grabar.py (tomas propias) y voces.py (voces del catálogo), con los criterios de docs/guiones/README.md.
"""

import re
import subprocess
import sys
from pathlib import Path

if (_SRC := str(Path(__file__).resolve().parents[1] / 'src')) not in sys.path:
    sys.path.insert(0, _SRC)
from content_studio.comun.ffmpeg import ffmpeg as _ffmpeg, loudness  # noqa: E402  (solo stdlib)

PISO_DB = (-90.0, -60.0)
BORDE_S = 0.4
LUFS_RANGO = (-20.0, -16.0)
LUFS_OBJ, TP_MAX = -18.0, -3.0


def medir(ruta: Path) -> dict:
    """Duración (s), pico (dB), piso de ruido del silencio inicial (dB) y pausas internas de 1 s o más."""
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                str(ruta)], capture_output=True, text=True, check=True).stdout)
    pico = float(re.search(r'max_volume: (-?[\d.]+|-inf) dB',
                           _ffmpeg('-i', str(ruta), '-af', 'volumedetect', '-f', 'null', '-'))[1])
    piso = float(re.search(r'mean_volume: (-?[\d.]+|-inf) dB',
                           _ffmpeg('-t', '0.3', '-i', str(ruta), '-af', 'volumedetect', '-f', 'null', '-'))[1])
    sil = _ffmpeg('-i', str(ruta), '-af', 'silencedetect=n=-45dB:d=1', '-f', 'null', '-')
    pausas = [float(d) for d in re.findall(r'silence_duration: ([\d.]+)', sil)]
    return {'duracion': dur, 'pico': pico, 'piso': piso, 'pausas': pausas}


def procesar(toma: Path, final: Path) -> None:
    """Recorta los bordes a 0.4 s y lleva la toma a -18 LUFS con pico real ≤ -3 dBTP, en WAV mono 48 kHz, 24 bits.

    La voz sin comprimir tiene picos (plosivas) unos 21-25 dB sobre su loudness, y la ganancia lineal sola
    solo cabe si esa distancia es ≤ 15 dB. Por eso: ganancia hasta el objetivo, limitador rápido que recorta
    solo esos transitorios, y una ganancia lineal final acotada por el pico, que siempre cabe."""
    recortada, limitada = final.with_suffix('.rec.wav'), final.with_suffix('.lim.wav')
    # Solo los bordes: el inicio, y el final dado vuelta. stop_periods=-1 comprimía también las pausas internas a
    # 0.4 s, lo que cambiaba el ritmo de la toma y escondía las pausas largas que verificar() debe detectar.
    borde = f'silenceremove=start_periods=1:start_threshold=-45dB:start_silence={BORDE_S}'
    recorte = f'{borde},areverse,{borde},areverse'
    formato = ['-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le']
    try:
        _ffmpeg('-y', '-i', str(toma), '-af', recorte, *formato, str(recortada))
        lufs, _ = loudness(recortada)
        techo = 10 ** ((TP_MAX - 2) / 20)  # 2 dB de margen: el limitador baja ~1-1.5 LU, y el pico real excede la muestra
        _ffmpeg('-y', '-i', str(recortada), '-af', f'aformat=sample_fmts=dbl,volume={LUFS_OBJ - lufs:.2f}dB,'
                f'alimiter=limit={techo:.4f}:level=0:attack=5:release=50', *formato, str(limitada))
        lufs, tp = loudness(limitada)
        _ffmpeg('-y', '-i', str(limitada), '-af', f'volume={min(LUFS_OBJ - lufs, TP_MAX - tp):.2f}dB',
                *formato, str(final))
    finally:
        recortada.unlink(missing_ok=True)
        limitada.unlink(missing_ok=True)


def verificar(final: Path, lo: float, hi: float, piso: bool = True) -> list[tuple[bool, str]]:
    """Criterios de docs/guiones/README.md sobre la referencia normalizada: (cumple, texto).
    `piso=False` no exige piso de ruido: un clip generado empieza en silencio digital."""
    m = medir(final)
    lufs, tp = loudness(final)
    codec, sr, canales = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,sample_rate,channels', '-of', 'csv=p=0',
         str(final)], capture_output=True, text=True, check=True).stdout.strip().split(',')
    checks = [
        (lo <= m['duracion'] <= hi, f'duración {m["duracion"]:.1f} s (guía: {lo}–{hi} s)'),
        (canales == '1' and sr == '48000' and codec == 'pcm_s24le', f'{canales} canal, {sr} Hz, {codec}'),
        (LUFS_RANGO[0] <= lufs <= LUFS_RANGO[1], f'loudness {lufs:.1f} LUFS (guía: −20 a −16)'),
        (tp <= TP_MAX, f'pico real {tp:.1f} dBTP (guía: ≤ −3)'),
        (not m['pausas'], 'sin pausas internas de 1 s o más' if not m['pausas']
         else f'pausa interna de {max(m["pausas"]):.1f} s (guía: ninguna de más de 1 s)'),
    ]
    if piso:
        checks.insert(4, (PISO_DB[0] < m['piso'] <= PISO_DB[1],
                          f'piso de ruido {m["piso"]:.0f} dB (guía: entre −90 y −60)'))
    return checks
