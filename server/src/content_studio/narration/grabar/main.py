r"""Graba las voces de referencia (server/data/narration/reference/<estilo>.wav) desde un dispositivo del equipo.

Uso:
    python cli.py narration grabar --list                # dispositivos de audio disponibles
    python cli.py narration grabar                         # elige dispositivo y estilos en el menú
    python cli.py narration grabar --device RDPSource --style neutral amistosa
    python cli.py narration grabar --device 2 --all # el kit completo, en el orden de la guía

Mientras graba muestra el texto, el tiempo contra la duración de la guía, el nivel y la forma de onda.
Cada toma se guarda en server/data/narration/reference/takes/ (gitignoreado).
Al aceptar una, se recortan los bordes a 0.4 s,
se normaliza a -18 LUFS (limitando solo los picos) y queda en
server/data/narration/reference/<estilo>.wav (WAV mono, 48 kHz, 24 bits).
Después se verifica con los criterios de docs/scripts/README.md. Usa ffmpeg, ffprobe y ffplay (escuchar).
"""

from __future__ import annotations

import argparse
import contextlib
import shutil
import subprocess
import sys

import questionary
from questionary import Choice, Separator
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from content_studio.common.files import next_number
from content_studio.narration.grabar.dispositivos import WINDOWS, sources
from content_studio.narration.grabar.interfaz import ACCENT, STYLE_Q, console, sheet_take
from content_studio.narration.grabar.kit import DURATION, KIT, OPTIONAL, SCRIPT, level_take
from content_studio.narration.grabar.toma import grabar_take
from content_studio.narration.reference import measure, process, verify
from content_studio.paths import REFERENCE, ROOT, TAKES


def choose_source(items: list[tuple[str, str, bool]], requested: str | None) -> str:
    """Nombre de la fuente: la pedida (por nombre o por número) o la que se elige en el menú."""
    if requested is None:
        predet = next((n for n, _, p in items if p), items[0][0])
        return questionary.select(
            'Micrófono', style=STYLE_Q, instruction='(↑↓ · enter)', default=predet,
            choices=[Choice([('', f'{n:<20}'), ('class:desc', d + ('  · predeterminado' if p else ''))], value=n)
                     for n, d, p in items],
        ).unsafe_ask()  # fmt: skip
    if requested.isdigit() and 1 <= int(requested) <= len(items):
        return items[int(requested) - 1][0]
    if any(name == requested for name, _, _ in items):
        return requested
    sys.exit(f'No hay un dispositivo "{requested}". Ver: python cli.py narration grabar --list')


def choose_styles() -> list[str]:
    """Casillas con el estado de cada referencia. Vienen marcadas las pendientes del kit."""

    def option(n: str, optional: bool) -> Choice:
        lo, hi = DURATION[n]
        done = (REFERENCE / f'{n}.wav').exists()
        state = ('● grabada (se reemplaza)' if done else '○ pendiente') + ('  · opcional' if optional else '')
        text = [('', f'{n:<13}'), ('class:desc', f'{lo:>2}–{hi} s   {state}')]
        return Choice(text, value=n, checked=not done and not optional)

    chosen = questionary.checkbox(
        'Referencias a grabar', style=STYLE_Q, instruction='(espacio marca · a todas · enter confirma)',
        choices=[*[option(n, False) for n, _, _ in KIT], Separator('  ' + '─' * 30),
                 *[option(n, True) for n, _, _ in OPTIONAL]],
        validate=lambda x: bool(x) or 'Marca al menos una',
        erase_when_done=True,  # su respuesta ("done (n selections)") va en inglés: se escribe la propia
    ).unsafe_ask()  # fmt: skip
    console.print(f'[bold {ACCENT}]?[/] [bold]Referencias a grabar[/] [green]{", ".join(chosen)}[/]')
    return chosen


def grabar_style(source: str, style: str, overwrite: bool, i: int, total: int) -> str:
    """Graba las tomas de un estilo hasta aceptar una, que se procesa y se verifica. Devuelve el resultado."""
    final = REFERENCE / f'{style}.wav'
    if final.exists() and not overwrite:
        question = questionary.confirm(f'{style} ya está grabada. ¿Reemplazarla?', default=False, style=STYLE_Q)
        if not question.unsafe_ask():
            return 'ya existía'
    lo, hi = DURATION[style]
    text = (REFERENCE / f'{style}.txt').read_text(encoding='utf-8').strip()
    sheet_style = Panel(
        Group(Text(text, style='bold'), Text(''),
              Text.from_markup(f'[dim]Duración {lo}–{hi} s · actitud en '
                               f'server/data/narration/docs/scripts/{SCRIPT[style]}\n'
                               'Graba 3 tomas seguidas y quédate con la más natural, no con la más actuada.[/]')),
        title=f'[bold {ACCENT}]{style}[/] [dim]· {i}/{total} · {source}[/]', title_align='left',
        border_style=ACCENT, padding=(1, 2))  # fmt: skip
    TAKES.mkdir(parents=True, exist_ok=True)
    n = next_number(TAKES, style)
    listen = shutil.which('ffplay')
    previa = None  # ficha de la toma anterior, para compararla con la siguiente
    while True:
        console.clear()  # una pantalla por toma: el panel en vivo necesita el alto completo
        console.print(sheet_style)
        if previa:
            console.print(previa)
        take = TAKES / f'{style}-{n}.wav'
        options = [Choice('●  Grabar', 'grabar'), Choice('↷  Saltar este estilo', 'saltar')]
        choice = questionary.select(f'Toma {n}', style=STYLE_Q, instruction='(↑↓ · enter)', choices=options)
        if choice.unsafe_ask() == 'saltar':
            return 'saltada'
        ok, levels = grabar_take(source, take, style, n, text)
        console.clear()
        console.print(sheet_style)
        if not ok:
            previa = Text.from_markup(
                f'[yellow]⚠ Toma {n} sin audio:[/] se paró antes de capturar o el dispositivo no entrega datos.'
            )
            take.unlink(missing_ok=True)
            n += 1
            continue
        m = measure(take)
        level = level_take(m['peak'])
        previa = sheet_take(n, m, style, levels)
        console.print(previa)
        while True:
            action = questionary.select('¿Qué hacemos con esta toma?', style=STYLE_Q, instruction='(↑↓ · enter)',
                                        default='use' if level == 'ok' else 'otra', choices=[
                Choice('✓  Usarla como referencia', 'use', disabled='no se oye nada' if level == 'silence' else None),
                Choice('▶  Escucharla', 'listen', disabled=None if listen else 'falta ffplay'),
                Choice('↻  Grabar otra toma', 'otra'),
                Choice('↷  Saltar este estilo', 'saltar')]).unsafe_ask()  # fmt: skip
            if action != 'listen':
                break
            with (
                console.status('Reproduciendo… (Ctrl+C para cortar)', spinner='dots'),
                contextlib.suppress(KeyboardInterrupt),
            ):
                subprocess.run([listen, '-nodisp', '-autoexit', '-loglevel', 'quiet', str(take)])
        if action == 'saltar':
            return 'saltada'
        if action == 'use':
            with console.status('Recortando, normalizando y verificando…', spinner='dots'):
                process(take, final)
                checks = verify(final, *DURATION[style])
            t = Table(box=None, padding=(0, 1), show_header=False)
            for meets, detail in checks:
                t.add_row(Text('✓' if meets else '✗', style='green' if meets else 'red'), detail)
            todo = all(c for c, _ in checks)
            title = f'[bold]{"✓" if todo else "⚠"} {final.relative_to(ROOT).as_posix()}[/]'
            border = 'green' if todo else 'yellow'
            console.print(Panel(t, title=title, title_align='left', border_style=border, padding=(0, 2)))
            return 'items' if todo else 'lista con observaciones'
        n += 1


def build_parser() -> argparse.ArgumentParser:
    """Flags del script. cli.py lo usa para mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='muestra los dispositivos de audio disponibles y sale')
    ap.add_argument('--device', help='nombre de la fuente (p. ej. RDPSource) o su número en --list')
    ap.add_argument('--style', nargs='+', choices=list(DURATION), metavar='STYLE',
                    help='referencias a grabar, p. ej. neutral amistosa (ver docs/scripts/README.md)')  # fmt: skip
    ap.add_argument('--all', action='store_true', help='graba el kit completo en el orden de la guía')
    ap.add_argument('--overwrite', action='store_true', help='reemplaza las referencias que ya existen')
    return ap


def show_devices(items: list[tuple[str, str, bool]]) -> None:
    t = Table(title='Dispositivos de audio', title_style=f'bold {ACCENT}', header_style='bold', border_style='grey35')
    t.add_column('#', justify='right', style='dim')
    t.add_column('Nombre (--device)', style='bold cyan')
    t.add_column('Descripción')
    t.add_column('')
    for i, (name, desc, pred) in enumerate(items, 1):
        t.add_row(str(i), name, desc, '[green]● predeterminado[/]' if pred else '')
    console.print(t)


def main() -> None:
    a = build_parser().parse_args()
    items = sources()
    if not items:
        sys.exit(
            'No hay micrófonos activos en el registro de Windows (MMDevices/Audio/Capture).'
            if WINDOWS
            else 'No hay fuentes de audio de PulseAudio o PipeWire (ffmpeg -sources pulse no devolvió nada).'
        )
    if a.list:
        show_devices(items)
        return
    if not sys.stdin.isatty():
        sys.exit('Grabar necesita una terminal interactiva.')
    results = []
    try:
        welcome = Text.from_markup(
            f'[bold {ACCENT}]🎤  Grabar voces de referencia[/]\n[dim]Se guardan en server/data/narration/reference/. '
            'Usa audífonos y un cuarto en silencio.[/]'
        )
        console.print(Panel(welcome, border_style=ACCENT, padding=(0, 2), expand=False))
        source = choose_source(items, a.device)
        interactive = not (a.all or a.style)
        styles = [n for n, _, _ in KIT] if a.all else (a.style or choose_styles())
        for i, style in enumerate(styles, 1):
            results.append((style, grabar_style(source, style, a.overwrite or interactive, i, len(styles))))
    except (KeyboardInterrupt, EOFError):
        console.print('\n[dim]Cancelado. Las tomas grabadas siguen en server/data/narration/reference/tomas/.[/]')
    if results:
        color = {'items': 'green', 'lista con observaciones': 'yellow'}
        t = Table(title='Summary', title_style=f'bold {ACCENT}', border_style='grey35', header_style='bold')
        t.add_column('Style', style='bold')
        t.add_column('Resultado')
        for style, r in results:
            t.add_row(style, f'[{color.get(r, "dim")}]{r}[/]')
        console.print(t)


if __name__ == '__main__':
    main()
