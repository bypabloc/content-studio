"""--help de un comando: los flags de su parser en una tabla."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from content_studio import paths
from content_studio.cli.args import empty, es_booleano, flags, required
from content_studio.cli.commands import Command
from content_studio.cli.widgets import ACCENT, console


def show_help(cmd: Command) -> None:
    """Imprime la ayuda del comando, con su resumen y sus flags."""
    mod = cmd.load()
    ap = mod.build_parser()
    # SUMMARY: resumen en inglés del parser (la ayuda de la CLI). Sin él, el primer párrafo del docstring.
    summary = getattr(mod, 'SUMMARY', None) or (mod.__doc__ or '').strip().split('\n\n')[0]
    t = Table(box=None, padding=(0, 2), show_header=True, header_style=f'bold {ACCENT}')
    t.add_column('Flag', style='bold cyan', no_wrap=True)
    t.add_column('Values', style='green', max_width=28)
    t.add_column('Default', style='dim', max_width=14)
    t.add_column('Descripción', ratio=1, overflow='fold')
    for acc in flags(ap):
        if es_booleano(acc):
            values = 'sí/no'
        elif acc.choices:
            values = ' · '.join(map(str, acc.choices))
        else:
            values = (acc.metavar or (acc.type.__name__ if acc.type else 'text')).lower()
        if acc.nargs in ('+', '*'):
            values += ' (varios)'
        default = acc.default
        if isinstance(default, Path):
            default = os.path.relpath(default, paths.ROOT)
        elif isinstance(default, list):
            default = ' '.join(map(str, default))
        mark = ' [red]*[/]' if required(acc, ap) else ''
        t.add_row(', '.join(acc.option_strings) + mark, values, '' if empty(default) else str(default), acc.help or '')
    pie = Text.from_markup(
        '[red]*[/] obligatorio · si falta, el asistente lo pregunta · '
        f'[bold]python cli.py {cmd.key}[/] sin flags abre el asistente'
    )
    console.print(
        Panel(
            Group(Text(summary, style='italic'), Text(''), t, Text(''), pie),
            title=f'{cmd.icon}  [bold]{cmd.key}[/] — {cmd.title}',
            title_align='left',
            border_style=ACCENT,
            padding=(1, 2),
        )
    )
