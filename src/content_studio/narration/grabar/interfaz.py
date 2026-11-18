"""Terminal de grabar: teclas sin Enter, colores, vúmetro, forma de onda y los paneles de rich."""

from __future__ import annotations

import math
import os
import sys
from contextlib import contextmanager

import questionary
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from content_studio.narration.grabar.kit import CONSEJO, DURACION, NIVEL_DB, SILENCIO_DB, nivel_toma

WINDOWS = os.name == 'nt'
if WINDOWS:
    import msvcrt
else:
    import select
    import termios
    import tty

console = Console(highlight=False)
ACENTO = '#a78bfa'
ESTILO_Q = questionary.Style([
    ('qmark', f'fg:{ACENTO} bold'), ('question', 'bold'), ('answer', 'fg:#34d399 bold'),
    ('pointer', f'fg:{ACENTO} bold'), ('highlighted', f'fg:{ACENTO} bold'), ('selected', 'fg:#34d399'),
    ('instruction', 'fg:#6b7280 italic'), ('separator', 'fg:#4b5563'), ('disabled', 'fg:#6b7280 italic'),
    ('desc', 'fg:#9ca3af'),
])  # fmt: skip
PISO_MEDIDOR = -60.0
BARRAS = '▁▂▃▄▅▆▇█'


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
        db = max(niveles[i : i + paso])
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


def vista_grabacion(estilo: str, n: int, texto: str, seg: float, niveles: list[float]) -> Panel:
    lo, hi = DURACION[estilo]
    actual = niveles[-1] if niveles else PISO_MEDIDOR
    maximo = max(niveles[-60:], default=PISO_MEDIDOR)
    punto = '●' if int(seg * 2) % 2 == 0 else '○'
    tiempo = Text.assemble(barra_tiempo(seg, lo, hi), f'  {seg:5.1f} s ', (f'guía {lo}–{hi} s', 'dim'))
    nivel = Text.assemble(
        barra_nivel(actual), f'  {actual:5.1f} dB ', (f'pico {maximo:.1f} ({nivel_toma(maximo)})', color_nivel(maximo))
    )
    return Panel(
        Group(
            Panel(Text(texto, style='bold'), border_style='grey35', padding=(1, 2)),
            Text(''),
            Text.assemble(('Tiempo  ', 'dim'), tiempo),
            Text.assemble(('Nivel   ', 'dim'), nivel),
            Text.assemble(('Onda    ', 'dim'), onda(niveles[-60:], 60)),
            Text(''),
            Text('Enter o espacio para parar · Ctrl+C también para', style='dim italic'),
        ),
        title=f'[bold red]{punto} REC[/]  [bold]{estilo}[/] · toma {n}',
        title_align='left',
        border_style='red',
        padding=(1, 2),
    )


def ficha_toma(n: int, m: dict, estilo: str, niveles: list[float]) -> Panel:
    lo, hi = DURACION[estilo]
    nivel = nivel_toma(m['pico'])
    dur_ok = lo <= m['duracion'] <= hi
    t = Table(box=None, padding=(0, 2), show_header=False)
    t.add_column(style='dim')
    t.add_column()
    t.add_row(
        'Duración',
        Text.assemble(
            (f'{m["duracion"]:.1f} s', 'green' if dur_ok else 'yellow'),
            (f'  guía {lo}–{hi} s (se recorta a 0.4 s por borde)', 'dim'),
        ),
    )
    t.add_row(
        'Pico', Text.assemble((f'{m["pico"]:.1f} dB  {nivel}', color_nivel(m['pico'])), (f'  {CONSEJO[nivel]}', 'dim'))
    )
    t.add_row('Onda', onda(niveles, 60))
    return Panel(
        t,
        title=f'[bold]Toma {n}[/]',
        title_align='left',
        border_style='green' if nivel == 'ok' and dur_ok else 'yellow',
        padding=(0, 2),
    )
