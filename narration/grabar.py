r"""Graba las voces de referencia (narration/voz/<estilo>.wav) desde un dispositivo de audio del equipo.

Uso:
    python narration/grabar.py --listar                    # dispositivos de audio disponibles
    python narration/grabar.py                             # elige dispositivo y estilo en el menú
    python narration/grabar.py --dispositivo RDPSource --estilo neutral amistosa
    python narration/grabar.py --dispositivo 2 --todos     # el kit completo, en el orden de la guía

Cada toma se guarda en narration/voz/tomas/ (gitignoreado). Al aceptar una, se recortan los bordes a 0.4 s,
se normaliza con ganancia lineal y queda en narration/voz/<estilo>.wav (WAV mono, 48 kHz, 24 bits).
Después se verifica con los criterios de docs/guiones/README.md. Solo usa ffmpeg y ffprobe.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
VOZ = AQUI / 'voz'
TOMAS = VOZ / 'tomas'

# Orden, duración (s) y guion con actitud de cada referencia (tabla de docs/guiones/README.md).
KIT = [
    ('neutral', 10, 12), ('amistosa', 9, 11), ('experta', 10, 12), ('clara', 10, 12), ('estable', 10, 11),
    ('suave', 10, 11), ('energica', 8, 10), ('dramatica', 10, 12), ('triste', 10, 12), ('intima', 9, 11),
    ('neutral-en', 10, 12), ('neutral-fin', 10, 12),
]
OPCIONAL = [('susurro', 7, 9)]
DURACION = {n: (lo, hi) for n, lo, hi in KIT + OPCIONAL}
GUION = {
    'neutral': '00-neutral.md', 'amistosa': '01-amistosa.md', 'suave': '02-suave.md', 'experta': '03-experta.md',
    'clara': '04-clara.md', 'estable': '05-estable.md', 'energica': '06-energica.md', 'dramatica': '07-dramatica.md',
    'triste': '08-triste.md', 'intima': '09-intima.md', 'neutral-en': '10-neutral-en.md',
    'neutral-fin': '00-neutral.md', 'susurro': '09-intima.md',
}
# Criterios de la guía: nivel de la toma cruda, piso de ruido, silencio digital y normalización.
NIVEL_DB = (-12.0, -6.0)
PISO_DB = (-90.0, -60.0)
SILENCIO_DB = -60.0
BORDE_S = 0.4
LUFS_RANGO = (-20.0, -16.0)
LUFS_OBJ, TP_MAX = -18.0, -3.0


def fuentes() -> list[tuple[str, str, bool]]:
    """Fuentes de PulseAudio o PipeWire, como las lista `ffmpeg -sources pulse`."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-sources', 'pulse'], capture_output=True, text=True)
    return parsear_fuentes(r.stdout + r.stderr)


def parsear_fuentes(texto: str) -> list[tuple[str, str, bool]]:
    """(nombre, descripción, predeterminada) de cada fuente. El * marca la predeterminada.

    >>> parsear_fuentes('Auto-detected sources for pulse:\\n  RDPSink.monitor [Monitor of RDP Sink] (none)\\n* RDPSource [RDP Source] (none)')
    [('RDPSink.monitor', 'Monitor of RDP Sink', False), ('RDPSource', 'RDP Source', True)]
    """
    return [(m[2], m[3], m[1] == '*') for m in re.finditer(r'^(\*?)\s*(\S+)\s+\[(.*?)\]', texto, re.M)]


def elegir_fuente(lista: list[tuple[str, str, bool]], pedida: str | None) -> str:
    """Nombre de la fuente: la pedida (por nombre o por número) o la que se elige en el menú."""
    if pedida is None:
        for i, (nombre, desc, pred) in enumerate(lista, 1):
            print(f'  {i}. {nombre} — {desc}{" (predeterminado)" if pred else ""}')
        predet = next((i for i, f in enumerate(lista, 1) if f[2]), 1)
        while True:
            resp = input(f'Dispositivo [{predet}]: ').strip() or str(predet)
            if resp.isdigit() and 1 <= int(resp) <= len(lista):
                return lista[int(resp) - 1][0]
            print('  Número fuera de la lista.')
    if pedida.isdigit() and 1 <= int(pedida) <= len(lista):
        return lista[int(pedida) - 1][0]
    if any(nombre == pedida for nombre, _, _ in lista):
        return pedida
    sys.exit(f'No hay un dispositivo "{pedida}". Ver: python narration/grabar.py --listar')


def elegir_estilos() -> list[str]:
    """Menú de referencias con su estado. Enter elige las pendientes del kit, en el orden de la guía."""
    nombres = [n for n, _, _ in KIT] + [n for n, _, _ in OPCIONAL]
    for i, n in enumerate(nombres, 1):
        estado = 'grabada' if (VOZ / f'{n}.wav').exists() else 'pendiente'
        print(f'  {i:2d}. {n:<12} {estado}')
    resp = input('Números separados por comas (Enter = pendientes del kit): ').strip()
    if not resp:
        return [n for n, _, _ in KIT if not (VOZ / f'{n}.wav').exists()]
    return [nombres[int(x) - 1] for x in resp.replace(' ', '').split(',')
            if x.isdigit() and 1 <= int(x) <= len(nombres)]


def grabar_toma(fuente: str, destino: Path) -> bool:
    """Graba desde `fuente` hasta que se pulse Enter (o Ctrl+C). ffmpeg cierra el WAV limpiamente con 'q'.
    Devuelve False si no llegó audio: la toma es demasiado corta o el dispositivo no entregó datos."""
    proc = subprocess.Popen(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'pulse', '-i', fuente,
         '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(destino)],
        stdin=subprocess.PIPE,
    )
    try:
        input()
    except KeyboardInterrupt:
        print()
    try:
        proc.stdin.write(b'q')
        proc.stdin.flush()
        proc.wait(timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        proc.kill()
        proc.wait()
    return destino.exists() and destino.stat().st_size > 4096


def _ffmpeg(*args: str) -> str:
    """Salida de error de ffmpeg: ahí escriben volumedetect, ebur128 y silencedetect."""
    return subprocess.run(['ffmpeg', '-hide_banner', '-nostats', *args],
                          capture_output=True, text=True, check=True).stderr


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


def loudness(ruta: Path) -> tuple[float, float]:
    """Loudness integrada (LUFS) y pico real (dBTP) con ebur128."""
    veri = _ffmpeg('-i', str(ruta), '-af', 'ebur128=peak=true', '-f', 'null', '-')
    return (float(re.search(r'^\s*I:\s+(-?[\d.]+) LUFS', veri, re.M)[1]),
            float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', veri)[1]))


def nivel_toma(pico: float) -> str:
    """Estado del pico de la toma cruda frente a la guía (de -12 a -6 dB).

    >>> [nivel_toma(p) for p in (-80.0, -20.0, -9.0, -3.0)]
    ['silencio', 'bajo', 'ok', 'alto']
    """
    if pico <= SILENCIO_DB:
        return 'silencio'
    if pico < NIVEL_DB[0]:
        return 'bajo'
    if pico > NIVEL_DB[1]:
        return 'alto'
    return 'ok'


def _json(stderr: str) -> dict:
    """loudnorm con print_format=json escribe su JSON al final de stderr."""
    return json.loads(stderr[stderr.rindex('{', 0, stderr.rindex('}')):stderr.rindex('}') + 1])


def procesar(toma: Path, final: Path) -> bool:
    """Recorta los bordes a 0.4 s y normaliza con ganancia lineal (-18 LUFS, pico ≤ -3 dBTP), en WAV mono
    48 kHz, 24 bits. Devuelve False si no pudo ser lineal: la toma tiene picos demasiado altos."""
    tmp = final.with_suffix('.tmp.wav')
    recorte = (f'silenceremove=start_periods=1:start_threshold=-45dB:start_silence={BORDE_S}'
               f':stop_periods=-1:stop_threshold=-45dB:stop_silence={BORDE_S}')
    formato = ['-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le']
    _ffmpeg('-y', '-i', str(toma), '-af', recorte, *formato, str(tmp))
    base = f'loudnorm=I={LUFS_OBJ}:TP={TP_MAX}:LRA=11'
    try:
        med = _json(_ffmpeg('-i', str(tmp), '-af', f'{base}:print_format=json', '-f', 'null', '-'))
        fin = _json(_ffmpeg('-y', '-i', str(tmp), '-af',
                            f'{base}:linear=true:measured_I={med["input_i"]}:measured_TP={med["input_tp"]}'
                            f':measured_LRA={med["input_lra"]}:measured_thresh={med["input_thresh"]}'
                            f':offset={med["target_offset"]}:print_format=json', *formato, str(final)))
    finally:
        tmp.unlink(missing_ok=True)
    return fin['normalization_type'] == 'linear'


def verificar(estilo: str, final: Path) -> list[tuple[bool, str]]:
    """Criterios de docs/guiones/README.md sobre la referencia normalizada: (cumple, texto)."""
    m = medir(final)
    lufs, tp = loudness(final)
    codec, sr, canales = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,sample_rate,channels', '-of', 'csv=p=0',
         str(final)], capture_output=True, text=True, check=True).stdout.strip().split(',')
    lo, hi = DURACION[estilo]
    return [
        (lo <= m['duracion'] <= hi, f'duración {m["duracion"]:.1f} s (guía: {lo}–{hi} s)'),
        (canales == '1' and sr == '48000' and codec == 'pcm_s24le', f'{canales} canal, {sr} Hz, {codec}'),
        (LUFS_RANGO[0] <= lufs <= LUFS_RANGO[1], f'loudness {lufs:.1f} LUFS (guía: −20 a −16)'),
        (tp <= TP_MAX, f'pico real {tp:.1f} dBTP (guía: ≤ −3)'),
        (PISO_DB[0] < m['piso'] <= PISO_DB[1], f'piso de ruido {m["piso"]:.0f} dB (guía: entre −90 y −60)'),
        (not m['pausas'], 'sin pausas internas de 1 s o más' if not m['pausas']
         else f'pausa interna de {max(m["pausas"]):.1f} s (guía: ninguna de más de 1 s)'),
    ]


def grabar_estilo(fuente: str, estilo: str, sobrescribir: bool) -> None:
    """Graba las tomas de un estilo hasta aceptar una, que se procesa y se verifica."""
    final = VOZ / f'{estilo}.wav'
    if final.exists() and not sobrescribir:
        print(f'\n[{estilo}] ya existe {final.relative_to(AQUI.parent)} (usa --sobrescribir para reemplazarla).')
        return
    lo, hi = DURACION[estilo]
    texto = (VOZ / f'{estilo}.txt').read_text(encoding='utf-8').strip()
    print(f'\n=== {estilo} · {lo}–{hi} s · actitud: narration/docs/guiones/{GUION[estilo]}')
    print(f'Texto, palabra por palabra:\n  {texto}')
    print('La guía pide 3 tomas seguidas y quedarte con la más natural.')
    TOMAS.mkdir(parents=True, exist_ok=True)
    n = len(list(TOMAS.glob(f'{estilo}-*.wav'))) + 1
    while True:
        toma = TOMAS / f'{estilo}-{n}.wav'
        input(f'\nToma {n}. Enter para empezar a grabar… ')
        print('● Grabando. Lee el texto y pulsa Enter para parar.')
        if not grabar_toma(fuente, toma):
            print(f'  toma {n}: sin audio (se paró antes de capturar o el dispositivo no entrega datos).')
            toma.unlink(missing_ok=True)
            n += 1
            continue
        m = medir(toma)
        nivel = nivel_toma(m['pico'])
        print(f'  toma {n}: {m["duracion"]:.1f} s, pico {m["pico"]:.1f} dB ({nivel})')
        if nivel == 'silencio':
            print('  No se oye nada: revisa el micrófono y el dispositivo elegido.')
        elif nivel == 'bajo':
            print('  Pico por debajo de −12 dB: acércate un poco al micrófono.')
        elif nivel == 'alto':
            print('  Pico por encima de −6 dB: aléjate un poco del micrófono.')
        resp = input('  Enter = usar esta toma · r = otra toma · s = saltar este estilo: ').strip().lower()
        if resp == 's':
            return
        if resp == '' and nivel != 'silencio':
            if procesar(toma, final):
                print(f'\nReferencia lista: {final.relative_to(AQUI.parent)}')
                for cumple, detalle in verificar(estilo, final):
                    print(f'  {"✓" if cumple else "✗"} {detalle}')
                return
            print('  La normalización no pudo ser lineal: la toma tiene picos demasiado altos.')
            print('  Repite alejándote un poco del micrófono.')
            final.unlink(missing_ok=True)
        n += 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--listar', action='store_true', help='muestra los dispositivos de audio disponibles y sale')
    ap.add_argument('--dispositivo', help='nombre de la fuente (p. ej. RDPSource) o su número en --listar')
    ap.add_argument('--estilo', nargs='+', choices=list(DURACION), metavar='ESTILO',
                    help='referencias a grabar, p. ej. neutral amistosa (ver docs/guiones/README.md)')
    ap.add_argument('--todos', action='store_true', help='graba el kit completo en el orden de la guía')
    ap.add_argument('--sobrescribir', action='store_true', help='reemplaza las referencias que ya existen')
    a = ap.parse_args()

    lista = fuentes()
    if not lista:
        sys.exit('No hay fuentes de audio de PulseAudio o PipeWire (ffmpeg -sources pulse no devolvió nada).')
    if a.listar:
        for i, (nombre, desc, pred) in enumerate(lista, 1):
            print(f'{i}. {nombre} — {desc}{" (predeterminado)" if pred else ""}')
        return
    try:
        fuente = elegir_fuente(lista, a.dispositivo)
        estilos = [n for n, _, _ in KIT] if a.todos else (a.estilo or elegir_estilos())
        for estilo in estilos:
            grabar_estilo(fuente, estilo, a.sobrescribir)
    except (KeyboardInterrupt, EOFError):
        print('\nCancelado. Las tomas grabadas siguen en narration/voz/tomas/.')


if __name__ == '__main__':
    main()
