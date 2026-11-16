# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=14", "questionary>=2.1"]
# ///
r"""Graba las voces de referencia (narration/voz/<estilo>.wav) desde un dispositivo de audio del equipo.

Uso:
    python cli.py narration grabar --listar                # dispositivos de audio disponibles
    python cli.py narration grabar                         # elige dispositivo y estilos en el menú
    python cli.py narration grabar --dispositivo RDPSource --estilo neutral amistosa
    python cli.py narration grabar --dispositivo 2 --todos # el kit completo, en el orden de la guía

Mientras graba muestra el texto, el tiempo contra la duración de la guía, el nivel y la forma de onda.
Cada toma se guarda en narration/voz/tomas/ (gitignoreado). Al aceptar una, se recortan los bordes a 0.4 s,
se normaliza con ganancia lineal y queda en narration/voz/<estilo>.wav (WAV mono, 48 kHz, 24 bits).
Después se verifica con los criterios de docs/guiones/README.md. Usa ffmpeg, ffprobe y ffplay (escuchar).
"""

import argparse
import json
import math
import os
import re
import select
import shutil
import subprocess
import sys
import termios
import tty
from array import array
from pathlib import Path

try:
    import questionary
    from questionary import Choice, Separator
    from rich.align import Align
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:  # python sin rich/questionary: uv los instala según la cabecera de arriba
    if __name__ == '__main__':
        os.execvp('uv', ['uv', 'run', '--quiet', '--script', __file__, *sys.argv[1:]])
    raise

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


console = Console(highlight=False)
ACENTO = '#a78bfa'
ESTILO_Q = questionary.Style([
    ('qmark', f'fg:{ACENTO} bold'), ('question', 'bold'), ('answer', 'fg:#34d399 bold'),
    ('pointer', f'fg:{ACENTO} bold'), ('highlighted', f'fg:{ACENTO} bold'), ('selected', 'fg:#34d399'),
    ('instruction', 'fg:#6b7280 italic'), ('separator', 'fg:#4b5563'), ('disabled', 'fg:#6b7280 italic'),
    ('desc', 'fg:#9ca3af'),
])
# Medidor en vivo: ffmpeg manda una copia a 16 kHz por la tubería; un bloque son 50 ms.
MUESTREO, BLOQUE_S = 16000, 0.05
PISO_MEDIDOR = -60.0
BARRAS = '▁▂▃▄▅▆▇█'


def color_nivel(db: float) -> str:
    """Color de un nivel frente a la guía: bajo, en rango (-12 a -6 dB) o alto."""
    return 'red' if db > NIVEL_DB[1] else 'green' if db >= NIVEL_DB[0] else 'cyan' if db > SILENCIO_DB else 'grey35'


def onda(niveles: list[float], ancho: int) -> Text:
    """Forma de onda con bloques: cada columna es el pico de su tramo, de -60 dB (▁) a 0 dB (█).

    >>> onda([-80.0, -30.0, 0.0], 3).plain
    '▁▅█'
    """
    if not niveles:
        return Text('·' * ancho, style='grey35')
    paso = max(1, math.ceil(len(niveles) / ancho))
    t = Text()
    for i in range(0, len(niveles), paso):
        db = max(niveles[i:i + paso])
        x = min(1.0, max(0.0, (db - PISO_MEDIDOR) / -PISO_MEDIDOR))
        t.append(BARRAS[round(x * (len(BARRAS) - 1))], style=color_nivel(db))
    return t


def barra_nivel(db: float, ancho: int = 40) -> Text:
    """Vúmetro: celdas llenas hasta el nivel actual, coloreadas por zona (la verde es la de la guía)."""
    t = Text()
    for i in range(ancho):
        celda = PISO_MEDIDOR + (i + 0.5) * -PISO_MEDIDOR / ancho
        t.append('█' if celda <= db else '░', style=color_nivel(celda) if celda <= db else 'grey23')
    return t


def barra_tiempo(seg: float, lo: float, hi: float, ancho: int = 40) -> Text:
    """Tiempo grabado contra la guía: amarillo antes de lo, verde dentro, rojo pasado de hi."""
    tope = hi * 1.25
    t = Text()
    for i in range(ancho):
        celda = (i + 0.5) * tope / ancho
        color = 'yellow' if celda < lo else 'green' if celda <= hi else 'red'
        t.append('▰' if celda <= seg else '▱', style=color if celda <= seg else 'grey30')
    return t


def elegir_fuente(lista: list[tuple[str, str, bool]], pedida: str | None) -> str:
    """Nombre de la fuente: la pedida (por nombre o por número) o la que se elige en el menú."""
    if pedida is None:
        predet = next((n for n, _, p in lista if p), lista[0][0])
        return questionary.select(
            'Micrófono', style=ESTILO_Q, instruction='(↑↓ · enter)', default=predet,
            choices=[Choice([('', f'{n:<20}'), ('class:desc', d + ('  · predeterminado' if p else ''))], value=n)
                     for n, d, p in lista],
        ).unsafe_ask()
    if pedida.isdigit() and 1 <= int(pedida) <= len(lista):
        return lista[int(pedida) - 1][0]
    if any(nombre == pedida for nombre, _, _ in lista):
        return pedida
    sys.exit(f'No hay un dispositivo "{pedida}". Ver: python cli.py narration grabar --listar')


def elegir_estilos() -> list[str]:
    """Casillas con el estado de cada referencia. Vienen marcadas las pendientes del kit."""
    def opcion(n: str, opcional: bool) -> Choice:
        lo, hi = DURACION[n]
        hecha = (VOZ / f'{n}.wav').exists()
        estado = ('● grabada (se reemplaza)' if hecha else '○ pendiente') + ('  · opcional' if opcional else '')
        return Choice([('', f'{n:<13}'), ('class:desc', f'{lo:>2}–{hi} s   {estado}')], value=n,
                      checked=not hecha and not opcional)
    elegidos = questionary.checkbox(
        'Referencias a grabar', style=ESTILO_Q, instruction='(espacio marca · a todas · enter confirma)',
        choices=[*[opcion(n, False) for n, _, _ in KIT], Separator('  ' + '─' * 30),
                 *[opcion(n, True) for n, _, _ in OPCIONAL]],
        validate=lambda x: bool(x) or 'Marca al menos una',
        erase_when_done=True,  # su respuesta ("done (n selections)") va en inglés: se escribe la propia
    ).unsafe_ask()
    console.print(f'[bold {ACENTO}]?[/] [bold]Referencias a grabar[/] [green]{", ".join(elegidos)}[/]')
    return elegidos


def vista_grabacion(estilo: str, n: int, texto: str, seg: float, niveles: list[float]) -> Panel:
    lo, hi = DURACION[estilo]
    actual = niveles[-1] if niveles else PISO_MEDIDOR
    maximo = max(niveles[-60:], default=PISO_MEDIDOR)
    punto = '●' if int(seg * 2) % 2 == 0 else '○'
    tiempo = Text.assemble(barra_tiempo(seg, lo, hi), f'  {seg:5.1f} s ', (f'guía {lo}–{hi} s', 'dim'))
    nivel = Text.assemble(barra_nivel(actual), f'  {actual:5.1f} dB ',
                          (f'pico {maximo:.1f} ({nivel_toma(maximo)})', color_nivel(maximo)))
    return Panel(
        Group(Panel(Text(texto, style='bold'), border_style='grey35', padding=(1, 2)), Text(''),
              Text.assemble(('Tiempo  ', 'dim'), tiempo), Text.assemble(('Nivel   ', 'dim'), nivel),
              Text.assemble(('Onda    ', 'dim'), onda(niveles[-60:], 60)), Text(''),
              Text('Enter o espacio para parar · Ctrl+C también para', style='dim italic')),
        title=f'[bold red]{punto} REC[/]  [bold]{estilo}[/] · toma {n}', title_align='left',
        border_style='red', padding=(1, 2))


def grabar_toma(fuente: str, destino: Path, estilo: str, n: int, texto: str) -> tuple[bool, list[float]]:
    """Graba desde `fuente` hasta Enter, espacio o Ctrl+C, con el panel en vivo. ffmpeg escribe el WAV y
    manda una copia a 16 kHz por stdout para medir el nivel; se cierra limpio con 'q'.
    Devuelve (llegó audio, niveles en dB por bloque de 50 ms)."""
    proc = subprocess.Popen(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'pulse', '-i', fuente,
         '-map', '0:a', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(destino),
         '-map', '0:a', '-ac', '1', '-ar', str(MUESTREO), '-f', 's16le', 'pipe:1'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )
    bloque = int(MUESTREO * BLOQUE_S) * 2
    niveles: list[float] = []
    pendiente = b''
    tecla = sys.stdin.fileno()
    modo = termios.tcgetattr(tecla)

    def vista():
        return Align.center(vista_grabacion(estilo, n, texto, len(niveles) * BLOQUE_S, niveles),
                            vertical='middle', height=console.size.height)
    try:
        tty.setcbreak(tecla)  # teclas sin Enter y sin eco; Ctrl+C sigue funcionando
        # Pantalla alternativa: cada frame se dibuja desde la esquina, sin mover el cursor relativo, así que
        # no deja restos aunque la terminal maneje distinto las líneas de ancho completo. Al parar, vuelve.
        with Live(vista(), console=console, refresh_per_second=20, screen=True) as live:
            while True:
                listos, _, _ = select.select([tecla, proc.stdout], [], [], 0.05)
                if tecla in listos and os.read(tecla, 1) in (b'\n', b'\r', b' '):
                    break
                if proc.stdout in listos:
                    dato = os.read(proc.stdout.fileno(), 8192)
                    if not dato:
                        break  # ffmpeg terminó solo: el dispositivo se cerró
                    pendiente += dato
                    while len(pendiente) >= bloque:
                        muestras = array('h', pendiente[:bloque])
                        pendiente = pendiente[bloque:]
                        pico = max(max(muestras), -min(muestras), 1)
                        niveles.append(20 * math.log10(pico / 32768))
                live.update(vista())
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(tecla, termios.TCSADRAIN, modo)
        try:
            proc.stdin.write(b'q')
            proc.stdin.flush()
            proc.communicate(timeout=10)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
    return destino.exists() and destino.stat().st_size > 4096, niveles


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


CONSEJO = {
    'silencio': 'No se oye nada: revisa el micrófono y el dispositivo elegido.',
    'bajo': 'Pico por debajo de −12 dB: acércate un poco al micrófono.',
    'alto': 'Pico por encima de −6 dB: aléjate un poco del micrófono.',
    'ok': 'Nivel dentro de la guía.',
}


def ficha_toma(n: int, m: dict, estilo: str, niveles: list[float]) -> Panel:
    lo, hi = DURACION[estilo]
    nivel = nivel_toma(m['pico'])
    dur_ok = lo <= m['duracion'] <= hi
    t = Table(box=None, padding=(0, 2), show_header=False)
    t.add_column(style='dim')
    t.add_column()
    t.add_row('Duración', Text.assemble((f'{m["duracion"]:.1f} s', 'green' if dur_ok else 'yellow'),
                                        (f'  guía {lo}–{hi} s (se recorta a 0.4 s por borde)', 'dim')))
    t.add_row('Pico', Text.assemble((f'{m["pico"]:.1f} dB  {nivel}', color_nivel(m['pico'])),
                                    (f'  {CONSEJO[nivel]}', 'dim')))
    t.add_row('Onda', onda(niveles, 60))
    return Panel(t, title=f'[bold]Toma {n}[/]', title_align='left',
                 border_style='green' if nivel == 'ok' and dur_ok else 'yellow', padding=(0, 2))


def grabar_estilo(fuente: str, estilo: str, sobrescribir: bool, i: int, total: int) -> str:
    """Graba las tomas de un estilo hasta aceptar una, que se procesa y se verifica. Devuelve el resultado."""
    final = VOZ / f'{estilo}.wav'
    if final.exists() and not sobrescribir and not questionary.confirm(
            f'{estilo} ya está grabada. ¿Reemplazarla?', default=False, style=ESTILO_Q).unsafe_ask():
        return 'ya existía'
    lo, hi = DURACION[estilo]
    texto = (VOZ / f'{estilo}.txt').read_text(encoding='utf-8').strip()
    ficha_estilo = Panel(
        Group(Text(texto, style='bold'), Text(''),
              Text.from_markup(f'[dim]Duración {lo}–{hi} s · actitud en narration/docs/guiones/{GUION[estilo]}\n'
                               'Graba 3 tomas seguidas y quédate con la más natural, no con la más actuada.[/]')),
        title=f'[bold {ACENTO}]{estilo}[/] [dim]· {i}/{total} · {fuente}[/]', title_align='left',
        border_style=ACENTO, padding=(1, 2))
    TOMAS.mkdir(parents=True, exist_ok=True)
    n = len(list(TOMAS.glob(f'{estilo}-*.wav'))) + 1
    escuchar = shutil.which('ffplay')
    previa = None  # ficha de la toma anterior, para compararla con la siguiente
    while True:
        console.clear()  # una pantalla por toma: el panel en vivo necesita el alto completo
        console.print(ficha_estilo)
        if previa:
            console.print(previa)
        toma = TOMAS / f'{estilo}-{n}.wav'
        if questionary.select(f'Toma {n}', style=ESTILO_Q, instruction='(↑↓ · enter)', choices=[
                Choice('●  Grabar', 'grabar'), Choice('↷  Saltar este estilo', 'saltar')]).unsafe_ask() == 'saltar':
            return 'saltada'
        ok, niveles = grabar_toma(fuente, toma, estilo, n, texto)
        console.clear()
        console.print(ficha_estilo)
        if not ok:
            previa = Text.from_markup(f'[yellow]⚠ Toma {n} sin audio:[/] se paró antes de capturar '
                                      'o el dispositivo no entrega datos.')
            toma.unlink(missing_ok=True)
            n += 1
            continue
        m = medir(toma)
        nivel = nivel_toma(m['pico'])
        previa = ficha_toma(n, m, estilo, niveles)
        console.print(previa)
        while True:
            accion = questionary.select('¿Qué hacemos con esta toma?', style=ESTILO_Q, instruction='(↑↓ · enter)',
                                        default='usar' if nivel == 'ok' else 'otra', choices=[
                Choice('✓  Usarla como referencia', 'usar', disabled='no se oye nada' if nivel == 'silencio' else None),
                Choice('▶  Escucharla', 'escuchar', disabled=None if escuchar else 'falta ffplay'),
                Choice('↻  Grabar otra toma', 'otra'),
                Choice('↷  Saltar este estilo', 'saltar')]).unsafe_ask()
            if accion != 'escuchar':
                break
            with console.status('Reproduciendo… (Ctrl+C para cortar)', spinner='dots'):
                try:
                    subprocess.run([escuchar, '-nodisp', '-autoexit', '-loglevel', 'quiet', str(toma)])
                except KeyboardInterrupt:
                    pass
        if accion == 'saltar':
            return 'saltada'
        if accion == 'usar':
            with console.status('Recortando, normalizando y verificando…', spinner='dots'):
                lineal = procesar(toma, final)
                checks = verificar(estilo, final) if lineal else []
            if lineal:
                t = Table(box=None, padding=(0, 1), show_header=False)
                for cumple, detalle in checks:
                    t.add_row(Text('✓' if cumple else '✗', style='green' if cumple else 'red'), detalle)
                todo = all(c for c, _ in checks)
                console.print(Panel(t, title=f'[bold]{"✓" if todo else "⚠"} {final.relative_to(AQUI.parent)}[/]',
                                    title_align='left', border_style='green' if todo else 'yellow', padding=(0, 2)))
                return 'lista' if todo else 'lista con observaciones'
            console.print('[red]✗ La normalización no pudo ser lineal: la toma tiene picos demasiado altos.[/] '
                          'Repite alejándote un poco del micrófono.')
            final.unlink(missing_ok=True)
        n += 1


def construir_parser() -> argparse.ArgumentParser:
    """Flags del script. cli.py lo usa para mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--listar', action='store_true', help='muestra los dispositivos de audio disponibles y sale')
    ap.add_argument('--dispositivo', help='nombre de la fuente (p. ej. RDPSource) o su número en --listar')
    ap.add_argument('--estilo', nargs='+', choices=list(DURACION), metavar='ESTILO',
                    help='referencias a grabar, p. ej. neutral amistosa (ver docs/guiones/README.md)')
    ap.add_argument('--todos', action='store_true', help='graba el kit completo en el orden de la guía')
    ap.add_argument('--sobrescribir', action='store_true', help='reemplaza las referencias que ya existen')
    return ap


def main() -> None:
    a = construir_parser().parse_args()
    lista = fuentes()
    if not lista:
        sys.exit('No hay fuentes de audio de PulseAudio o PipeWire (ffmpeg -sources pulse no devolvió nada).')
    if a.listar:
        t = Table(title='Dispositivos de audio', title_style=f'bold {ACENTO}', header_style='bold', border_style='grey35')
        t.add_column('#', justify='right', style='dim')
        t.add_column('Nombre (--dispositivo)', style='bold cyan')
        t.add_column('Descripción')
        t.add_column('')
        for i, (nombre, desc, pred) in enumerate(lista, 1):
            t.add_row(str(i), nombre, desc, '[green]● predeterminado[/]' if pred else '')
        console.print(t)
        return
    if not sys.stdin.isatty():
        sys.exit('Grabar necesita una terminal interactiva.')
    resultados = []
    try:
        console.print(Panel(Text.from_markup(
            f'[bold {ACENTO}]🎤  Grabar voces de referencia[/]\n[dim]Se guardan en narration/voz/. '
            'Usa audífonos y un cuarto en silencio.[/]'), border_style=ACENTO, padding=(0, 2), expand=False))
        fuente = elegir_fuente(lista, a.dispositivo)
        interactivo = not (a.todos or a.estilo)
        estilos = [n for n, _, _ in KIT] if a.todos else (a.estilo or elegir_estilos())
        for i, estilo in enumerate(estilos, 1):
            resultados.append((estilo, grabar_estilo(fuente, estilo, a.sobrescribir or interactivo, i, len(estilos))))
    except (KeyboardInterrupt, EOFError):
        console.print('\n[dim]Cancelado. Las tomas grabadas siguen en narration/voz/tomas/.[/]')
    if resultados:
        color = {'lista': 'green', 'lista con observaciones': 'yellow'}
        t = Table(title='Resumen', title_style=f'bold {ACENTO}', border_style='grey35', header_style='bold')
        t.add_column('Estilo', style='bold')
        t.add_column('Resultado')
        for estilo, r in resultados:
            t.add_row(estilo, f'[{color.get(r, "dim")}]{r}[/]')
        console.print(t)


if __name__ == '__main__':
    main()
