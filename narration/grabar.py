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
se normaliza a -18 LUFS (limitando solo los picos) y queda en narration/voz/<estilo>.wav (WAV mono, 48 kHz, 24 bits).
Después se verifica con los criterios de docs/guiones/README.md. Usa ffmpeg, ffprobe y ffplay (escuchar).
"""

import argparse
import math
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
from array import array
from contextlib import contextmanager
from pathlib import Path

from referencia import medir, procesar, siguiente_numero, verificar

WINDOWS = os.name == 'nt'
if WINDOWS:
    import msvcrt
else:
    import select
    import termios
    import tty

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
        args = ['uv', 'run', '--quiet', '--script', __file__, *sys.argv[1:]]
        if WINDOWS:  # Windows no tiene exec: el padre espera al hijo y le deja el Ctrl+C
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            sys.exit(subprocess.call(args))
        os.execvp('uv', args)
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
# Criterios de la guía para la toma cruda: nivel y silencio digital. Los de la referencia final, en referencia.py.
NIVEL_DB = (-12.0, -6.0)
SILENCIO_DB = -60.0


def fuentes() -> list[tuple[str, str, bool]]:
    """Micrófonos activos (Windows) o fuentes de PulseAudio/PipeWire (Linux, WSL)."""
    if WINDOWS:
        return microfonos_windows()
    r = subprocess.run(['ffmpeg', '-hide_banner', '-sources', 'pulse'], capture_output=True, text=True)
    return parsear_fuentes(r.stdout + r.stderr)


def microfonos_windows() -> list[tuple[str, str, bool]]:
    """Micrófonos activos según el registro (MMDevices), con el nombre que usa DirectShow: "<desc> (<interfaz>)".
    No se listan con `ffmpeg -list_devices true -f dshow`, porque ffmpeg se cae (0xC0000005) al enumerar
    algunas cámaras virtuales antes de llegar al audio."""
    import winreg
    base = r'SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture'
    lista = []
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
        for i in range(winreg.QueryInfoKey(k)[0]):
            with winreg.OpenKey(k, winreg.EnumKey(k, i)) as d, winreg.OpenKey(d, 'Properties') as p:
                if winreg.QueryValueEx(d, 'DeviceState')[0] != 1:  # 1 = activo; desactivado/desconectado no
                    continue
                desc = winreg.QueryValueEx(p, '{a45c254e-df1c-4efd-8020-67d146a850e0},2')[0]
                interfaz = winreg.QueryValueEx(p, '{b3f8fa53-0004-438e-9003-51a46e139bfc},6')[0]
                lista.append((f'{desc} ({interfaz})', 'DirectShow', False))
    return sorted(lista)


def entrada(fuente: str) -> list[str]:
    """Flags de entrada de ffmpeg para grabar de `fuente`. En DirectShow, un búfer de 50 ms para que el
    vúmetro no vaya medio segundo atrasado."""
    if WINDOWS:
        return ['-f', 'dshow', '-audio_buffer_size', '50', '-i', f'audio={fuente}']
    return ['-f', 'pulse', '-i', fuente]


@contextmanager
def teclado_crudo():
    """Teclas sin Enter y sin eco mientras se graba; Ctrl+C sigue funcionando. En Windows, msvcrt ya las lee así."""
    if WINDOWS:
        yield
        return
    fd = sys.stdin.fileno()
    modo = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, modo)


def tecla_parar() -> bool:
    """True si se pulsó Enter o espacio (sin bloquear)."""
    if WINDOWS:
        return msvcrt.kbhit() and msvcrt.getwch() in '\r\n '
    fd = sys.stdin.fileno()
    return bool(select.select([fd], [], [], 0)[0]) and os.read(fd, 1) in (b'\n', b'\r', b' ')


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
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *entrada(fuente),
         '-map', '0:a', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(destino),
         '-map', '0:a', '-ac', '1', '-ar', str(MUESTREO), '-f', 's16le', 'pipe:1'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )
    bloque = int(MUESTREO * BLOQUE_S) * 2
    niveles: list[float] = []
    pendiente = b''
    # Un hilo lee el audio: select() no sirve con tuberías en Windows. b'' marca que ffmpeg terminó.
    cola: queue.Queue[bytes] = queue.Queue()

    def leer():
        try:
            while dato := proc.stdout.read1(8192):
                cola.put(dato)
        except (OSError, ValueError):  # communicate() cerró la tubería al parar
            pass
        cola.put(b'')
    threading.Thread(target=leer, daemon=True).start()

    def vista():
        return Align.center(vista_grabacion(estilo, n, texto, len(niveles) * BLOQUE_S, niveles),
                            vertical='middle', height=console.size.height)
    try:
        # Pantalla alternativa: cada frame se dibuja desde la esquina, sin mover el cursor relativo, así que
        # no deja restos aunque la terminal maneje distinto las líneas de ancho completo. Al parar, vuelve.
        with teclado_crudo(), Live(vista(), console=console, refresh_per_second=20, screen=True) as live:
            terminado = False
            while not terminado and not tecla_parar():
                try:
                    datos = [cola.get(timeout=BLOQUE_S)]
                    while not cola.empty():
                        datos.append(cola.get_nowait())
                except queue.Empty:
                    datos = []
                for dato in datos:
                    if not dato:
                        terminado = True  # ffmpeg terminó solo: el dispositivo se cerró
                        break
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
        try:
            proc.stdin.write(b'q')
            proc.stdin.flush()
            proc.communicate(timeout=10)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
    return destino.exists() and destino.stat().st_size > 4096, niveles


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
    n = siguiente_numero(TOMAS, estilo)
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
                procesar(toma, final)
                checks = verificar(final, *DURACION[estilo])
            t = Table(box=None, padding=(0, 1), show_header=False)
            for cumple, detalle in checks:
                t.add_row(Text('✓' if cumple else '✗', style='green' if cumple else 'red'), detalle)
            todo = all(c for c, _ in checks)
            console.print(Panel(t, title=f'[bold]{"✓" if todo else "⚠"} {final.relative_to(AQUI.parent)}[/]',
                                title_align='left', border_style='green' if todo else 'yellow', padding=(0, 2)))
            return 'lista' if todo else 'lista con observaciones'
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
        sys.exit('No hay micrófonos de DirectShow (ffmpeg -list_devices true -f dshow no devolvió nada).' if WINDOWS
                 else 'No hay fuentes de audio de PulseAudio o PipeWire (ffmpeg -sources pulse no devolvió nada).')
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
