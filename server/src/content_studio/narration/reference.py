"""Medición, normalización y verificación de una referencia de voz. Solo stdlib + ffmpeg.

Lo usan grabar (tomas propias) y voces.construir (voces del catálogo), con los criterios de docs/scripts/README.md.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from content_studio.common.ffmpeg import ffmpeg as _ffmpeg
from content_studio.common.ffmpeg import loudness

FLOOR_DB = (-90.0, -60.0)
BORDER_S = 0.4
LUFS_RANGE = (-20.0, -16.0)
LUFS_OBJ, TP_MAX = -18.0, -3.0


def measure(path: Path) -> dict:
    """Duración (s), pico (dB), piso de ruido del silencio inicial (dB) y pausas internas de 1 s o más."""
    dur = float(
        subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    peak = float(
        re.search(
            r'max_volume: (-?[\d.]+|-inf) dB', _ffmpeg('-i', str(path), '-af', 'volumedetect', '-f', 'null', '-')
        )[1]
    )
    floor = float(
        re.search(
            r'mean_volume: (-?[\d.]+|-inf) dB',
            _ffmpeg('-t', '0.3', '-i', str(path), '-af', 'volumedetect', '-f', 'null', '-'),
        )[1]
    )
    sil = _ffmpeg('-i', str(path), '-af', 'silencedetect=n=-45dB:d=1', '-f', 'null', '-')
    pauses = [float(d) for d in re.findall(r'silence_duration: ([\d.]+)', sil)]
    return {'duration': dur, 'peak': peak, 'floor': floor, 'pauses': pauses}


def process(take: Path, final: Path) -> None:
    """Recorta los bordes a 0.4 s y lleva la toma a -18 LUFS con pico real ≤ -3 dBTP, en WAV mono 48 kHz, 24 bits.

    La voz sin comprimir tiene picos (plosivas) unos 21-25 dB sobre su loudness, y la ganancia lineal sola
    solo cabe si esa distancia es ≤ 15 dB. Por eso: ganancia hasta el objetivo, limitador rápido que recorta
    solo esos transitorios, y una ganancia lineal final acotada por el pico, que siempre cabe."""
    trimmed, limited = final.with_suffix('.rec.wav'), final.with_suffix('.lim.wav')
    # Solo los bordes: el inicio, y el final dado vuelta. stop_periods=-1 comprimía también las pausas internas a
    # 0.4 s, lo que cambiaba el ritmo de la toma y escondía las pausas largas que verificar() debe detectar.
    border = f'silenceremove=start_periods=1:start_threshold=-45dB:start_silence={BORDER_S}'
    trim = f'{border},areverse,{border},areverse'
    format = ['-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le']
    try:
        _ffmpeg('-y', '-i', str(take), '-af', trim, *format, str(trimmed))
        lufs, _ = loudness(trimmed)
        # 2 dB de margen: el limitador baja ~1-1.5 LU, y el pico real excede la muestra
        ceiling = 10 ** ((TP_MAX - 2) / 20)
        _ffmpeg(
            '-y',
            '-i',
            str(trimmed),
            '-af',
            f'aformat=sample_fmts=dbl,volume={LUFS_OBJ - lufs:.2f}dB,'
            f'alimiter=limit={ceiling:.4f}:level=0:attack=5:release=50',
            *format,
            str(limited),
        )
        lufs, tp = loudness(limited)
        _ffmpeg(
            '-y', '-i', str(limited), '-af', f'volume={min(LUFS_OBJ - lufs, TP_MAX - tp):.2f}dB', *format, str(final)
        )
    finally:
        trimmed.unlink(missing_ok=True)
        limited.unlink(missing_ok=True)


def verify(final: Path, lo: float, hi: float, floor: bool = True) -> list[tuple[bool, str]]:
    """Criterios de docs/scripts/README.md sobre la referencia normalizada: (cumple, texto).
    `piso=False` no exige piso de ruido: un clip generado empieza en silencio digital."""
    m = measure(final)
    lufs, tp = loudness(final)
    codec, sr, channels = (
        subprocess.run(
            [
                'ffprobe',
                '-v',
                'error',
                '-show_entries',
                'stream=codec_name,sample_rate,channels',
                '-of',
                'csv=p=0',
                str(final),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
        .split(',')
    )
    checks = [
        (lo <= m['duration'] <= hi, f'duration {m["duration"]:.1f} s (guide: {lo}–{hi} s)'),
        (channels == '1' and sr == '48000' and codec == 'pcm_s24le', f'{channels} canal, {sr} Hz, {codec}'),
        (LUFS_RANGE[0] <= lufs <= LUFS_RANGE[1], f'loudness {lufs:.1f} LUFS (guide: −20 to −16)'),
        (tp <= TP_MAX, f'true peak {tp:.1f} dBTP (guide: ≤ −3)'),
        (
            not m['pauses'],
            'no internal pauses of 1 s or more'
            if not m['pauses']
            else f'internal pause of {max(m["pauses"]):.1f} s (guide: none longer than 1 s)',
        ),
    ]
    if floor:
        checks.insert(
            4,
            (FLOOR_DB[0] < m['floor'] <= FLOOR_DB[1], f'noise floor {m["floor"]:.0f} dB (guide: between −90 and −60)'),
        )
    return checks
