"""--help de un comando: los flags de su parser en una tabla."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from content_studio import rutas
from content_studio.cli.args import es_booleano, flags, obligatorio, vacio
from content_studio.cli.comandos import Comando
from content_studio.cli.widgets import ACENTO, console


def ayuda(cmd: Comando) -> None:
    mod = cmd.cargar()
    ap = mod.construir_parser()
    resumen = (mod.__doc__ or '').strip().split('\n\n')[0]
    t = Table(box=None, padding=(0, 2), show_header=True, header_style=f'bold {ACENTO}')
    t.add_column('Flag', style='bold cyan', no_wrap=True)
    t.add_column('Valores', style='green', max_width=28)
    t.add_column('Defecto', style='dim', max_width=14)
    t.add_column('Descripción', ratio=1, overflow='fold')
    for acc in flags(ap):
        if es_booleano(acc):
            valores = 'sí/no'
        elif acc.choices:
            valores = ' · '.join(map(str, acc.choices))
        else:
            valores = (acc.metavar or (acc.type.__name__ if acc.type else 'texto')).lower()
        if acc.nargs in ('+', '*'):
            valores += ' (varios)'
        defecto = acc.default
        if isinstance(defecto, Path):
            defecto = os.path.relpath(defecto, rutas.RAIZ)
        elif isinstance(defecto, list):
            defecto = ' '.join(map(str, defecto))
        marca = ' [red]*[/]' if obligatorio(acc, ap) else ''
        t.add_row(
            ', '.join(acc.option_strings) + marca, valores, '' if vacio(defecto) else str(defecto), acc.help or ''
        )
    pie = Text.from_markup(
        '[red]*[/] obligatorio · si falta, el asistente lo pregunta · '
        f'[bold]python cli.py {cmd.clave}[/] sin flags abre el asistente'
    )
    console.print(
        Panel(
            Group(Text(resumen, style='italic'), Text(''), t, Text(''), pie),
            title=f'{cmd.icono}  [bold]{cmd.clave}[/] — {cmd.titulo}',
            title_align='left',
            border_style=ACENTO,
            padding=(1, 2),
        )
    )
