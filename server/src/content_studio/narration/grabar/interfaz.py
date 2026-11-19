"""Terminal de grabar: teclas sin Enter, colores, vúmetro, forma de onda y los paneles de rich."""

from __future__ import annotations

import math
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager

import questionary
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from content_studio.narration.grabar.kit import DURATION, LEVEL_DB, SILENCE_DB, TIP, level_take

WINDOWS = os.name == 'nt'
if WINDOWS:
    import msvcrt
else:
    import select
    import termios
    import tty

console = Console(highlight=False)
ACCENT = '#a78bfa'
STYLE_Q = questionary.Style([
    ('qmark', f'fg:{ACCENT} bold'), ('question', 'bold'), ('answer', 'fg:#34d399 bold'),
    ('pointer', f'fg:{ACCENT} bold'), ('highlighted', f'fg:{ACCENT} bold'), ('selected', 'fg:#34d399'),
    ('instruction', 'fg:#6b7280 italic'), ('separator', 'fg:#4b5563'), ('disabled', 'fg:#6b7280 italic'),
    ('desc', 'fg:#9ca3af'),
])  # fmt: skip
FLOOR_MEDIDOR = -60.0
BARS = '▁▂▃▄▅▆▇█'


@contextmanager
def keyboard_raw() -> Iterator[None]:
    """Teclas sin Enter y sin eco mientras se graba; Ctrl+C sigue funcionando. En Windows, msvcrt ya las lee así."""
    if WINDOWS:
        yield
        return
    fd = sys.stdin.fileno()
    mode = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, mode)


def key_parar() -> bool:
    """True si se pulsó Enter o espacio (sin bloquear)."""
    if WINDOWS:
        return msvcrt.kbhit() and msvcrt.getwch() in '\r\n '
    fd = sys.stdin.fileno()
    return bool(select.select([fd], [], [], 0)[0]) and os.read(fd, 1) in (b'\n', b'\r', b' ')


def color_level(db: float) -> str:
    """Color de un nivel frente a la guía: bajo, en rango (-12 a -6 dB) o alto."""
    return 'red' if db > LEVEL_DB[1] else 'green' if db >= LEVEL_DB[0] else 'cyan' if db > SILENCE_DB else 'grey35'


def onda(levels: list[float], width: int) -> Text:
    """Forma de onda con bloques: cada columna es el pico de su tramo, de -60 dB (▁) a 0 dB (█).

    >>> onda([-80.0, -30.0, 0.0], 3).plain
    '▁▅█'
    """
    if not levels:
        return Text('·' * width, style='grey35')
    step = max(1, math.ceil(len(levels) / width))
    t = Text()
    for i in range(0, len(levels), step):
        db = max(levels[i : i + step])
        x = min(1.0, max(0.0, (db - FLOOR_MEDIDOR) / -FLOOR_MEDIDOR))
        t.append(BARS[round(x * (len(BARS) - 1))], style=color_level(db))
    return t


def bar_level(db: float, width: int = 40) -> Text:
    """Vúmetro: celdas llenas hasta el nivel actual, coloreadas por zona (la verde es la de la guía)."""
    t = Text()
    for i in range(width):
        cell = FLOOR_MEDIDOR + (i + 0.5) * -FLOOR_MEDIDOR / width
        t.append('█' if cell <= db else '░', style=color_level(cell) if cell <= db else 'grey23')
    return t


def bar_time(seg: float, lo: float, hi: float, width: int = 40) -> Text:
    """Tiempo grabado contra la guía: amarillo antes de lo, verde dentro, rojo pasado de hi."""
    cap = hi * 1.25
    t = Text()
    for i in range(width):
        cell = (i + 0.5) * cap / width
        color = 'yellow' if cell < lo else 'green' if cell <= hi else 'red'
        t.append('▰' if cell <= seg else '▱', style=color if cell <= seg else 'grey30')
    return t


def view_recording(style: str, n: int, text: str, seg: float, levels: list[float]) -> Panel:
    """Panel de la toma en curso: nivel, duración y línea de tiempo del estilo."""
    lo, hi = DURATION[style]
    current = levels[-1] if levels else FLOOR_MEDIDOR
    maximum = max(levels[-60:], default=FLOOR_MEDIDOR)
    point = '●' if int(seg * 2) % 2 == 0 else '○'
    time = Text.assemble(bar_time(seg, lo, hi), f'  {seg:5.1f} s ', (f'guía {lo}–{hi} s', 'dim'))
    level = Text.assemble(
        bar_level(current),
        f'  {current:5.1f} dB ',
        (f'pico {maximum:.1f} ({level_take(maximum)})', color_level(maximum)),
    )
    return Panel(
        Group(
            Panel(Text(text, style='bold'), border_style='grey35', padding=(1, 2)),
            Text(''),
            Text.assemble(('Tiempo  ', 'dim'), time),
            Text.assemble(('Nivel   ', 'dim'), level),
            Text.assemble(('Onda    ', 'dim'), onda(levels[-60:], 60)),
            Text(''),
            Text('Enter o espacio para parar · Ctrl+C también para', style='dim italic'),
        ),
        title=f'[bold red]{point} REC[/]  [bold]{style}[/] · toma {n}',
        title_align='left',
        border_style='red',
        padding=(1, 2),
    )


def sheet_take(n: int, m: dict, style: str, levels: list[float]) -> Panel:
    """Panel con la ficha de una toma ya grabada: pico, duración y nivel."""
    lo, hi = DURATION[style]
    level = level_take(m['peak'])
    dur_ok = lo <= m['duration'] <= hi
    t = Table(box=None, padding=(0, 2), show_header=False)
    t.add_column(style='dim')
    t.add_column()
    t.add_row(
        'Duración',
        Text.assemble(
            (f'{m["duration"]:.1f} s', 'green' if dur_ok else 'yellow'),
            (f'  guía {lo}–{hi} s (se recorta a 0.4 s por borde)', 'dim'),
        ),
    )
    t.add_row(
        'Peak', Text.assemble((f'{m["peak"]:.1f} dB  {level}', color_level(m['peak'])), (f'  {TIP[level]}', 'dim'))
    )
    t.add_row('Onda', onda(levels, 60))
    return Panel(
        t,
        title=f'[bold]Toma {n}[/]',
        title_align='left',
        border_style='green' if level == 'ok' and dur_ok else 'yellow',
        padding=(0, 2),
    )
