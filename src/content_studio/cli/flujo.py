"""Ejecutar un comando: directo, o con el asistente que pregunta lo que falta y muestra un resumen editable."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import questionary
import typer
from questionary import Choice, Separator
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from content_studio import rutas
from content_studio.cli.args import a_argv, flags, leer, vacio, validar
from content_studio.cli.ayuda import ayuda
from content_studio.cli.comandos import Comando
from content_studio.cli.widgets import ACENTO, ESTILO, SEPARADOR, console, preguntar, titulo
from content_studio.comun.proceso import env_src, relanzar, unir


def resumen(ap, valores: dict, cmd: Comando) -> Panel:
    t = Table(box=None, padding=(0, 2), show_header=False)
    t.add_column(style='bold cyan', no_wrap=True)
    t.add_column(ratio=1)
    for acc in flags(ap):
        dado = acc.dest in valores and not vacio(valores[acc.dest])
        v = valores[acc.dest] if dado else acc.default
        if vacio(v):
            continue
        if v is True:
            v = 'sí'
        elif isinstance(v, list):
            v = ' '.join(map(str, v))
        else:
            v = os.path.relpath(v, rutas.RAIZ) if isinstance(v, Path) and v.is_absolute() else str(v)
        v = v if len(v) < 300 else v[:297] + '…'
        t.add_row(
            Text(acc.option_strings[0], style='bold cyan' if dado else 'dim'),
            Text(v, style='green') if dado else Text.assemble((v, 'dim'), ('  por defecto', 'dim italic')),
        )
    comando = unir(['python', 'cli.py', *cmd.clave.split(), *a_argv(ap, valores)])
    return Panel(
        Group(t, Text(''), Text('$ ' + comando, style='dim')),
        title=f'{cmd.icono}  [bold]{cmd.clave}[/]',
        title_align='left',
        border_style=ACENTO,
        padding=(1, 2),
    )


def _obligatorios(ap, valores: dict, cat: dict) -> None:
    """Pregunta los obligatorios que faltan, en el orden del parser. Un grupo excluyente es una elección previa."""
    for acc in flags(ap):
        grupo = next((g for g in ap._mutually_exclusive_groups if g.required and acc in g._group_actions), None)
        if grupo:
            if any(valores.get(a.dest) is not None for a in grupo._group_actions):
                continue
            acc = questionary.select(
                '¿De dónde sale el contenido?',
                style=ESTILO,
                instruction='(↑↓ · enter)',
                choices=[Choice(titulo(a.option_strings[0], a.help or ''), value=a) for a in grupo._group_actions],
            ).unsafe_ask()
        elif not acc.required or valores.get(acc.dest) is not None:
            continue
        valores[acc.dest] = preguntar(acc, cat, None)


def _editar(ap, valores: dict, cat: dict) -> None:
    """Elige una opción y la vuelve a preguntar. --archivo reemplaza a --texto y viceversa."""
    opciones = []
    for acc in flags(ap):
        v = valores.get(acc.dest)
        if vacio(v):
            estado = acc.help or ''
        else:
            estado = '✓ ' + (' '.join(map(str, v)) if isinstance(v, list) else 'sí' if v is True else str(v))
        opciones.append(Choice(titulo(acc.option_strings[0], estado[:90]), value=acc))
    acc = questionary.select(
        '¿Qué opción?',
        choices=[*opciones, Separator(SEPARADOR), Choice('↩  Volver', None)],
        style=ESTILO,
        instruction='(↑↓ · enter)',
    ).unsafe_ask()
    if acc is None:
        return
    valores[acc.dest] = preguntar(acc, cat, valores.get(acc.dest))
    for g in ap._mutually_exclusive_groups:
        if acc in g._group_actions and valores[acc.dest] is not None:
            for otro in g._group_actions:
                if otro is not acc:
                    valores.pop(otro.dest, None)


def asistente(cmd: Comando, args: list[str], forzar: bool = False) -> None:
    mod = cmd.cargar()
    ap = mod.construir_parser()
    if not forzar and validar(mod, args) is None:
        lanzar(cmd, args)
    valores, avisos = leer(mod.construir_parser(), args)
    for aviso in avisos:
        console.print(f'[yellow]⚠ {aviso}[/]')
    cat = cmd.catalogo(mod)
    console.print(f'\n{cmd.icono}  [bold]{cmd.titulo}[/]  [dim]{cmd.desc}[/]\n')
    _obligatorios(ap, valores, cat)
    while True:  # resumen editable hasta ejecutar, redibujado en su lugar
        console.clear()
        console.print(resumen(ap, valores, cmd))
        argv = a_argv(ap, valores)
        error = validar(mod, argv)
        if error:
            console.print(f'[red]✗ {error}[/]')
        accion = questionary.select(
            '¿Qué hacemos?',
            style=ESTILO,
            instruction='(↑↓ · enter)',
            choices=[
                Choice('▶  Ejecutar', 'ejecutar', disabled='corrige el error' if error else None),
                Choice('✎  Agregar o cambiar una opción', 'editar'),
                Choice('✕  Cancelar', 'cancelar'),
            ],
        ).unsafe_ask()
        if accion == 'ejecutar':
            lanzar(cmd, argv)
        if accion == 'cancelar':
            cancelar()
        _editar(ap, valores, cat)


def lanzar(cmd: Comando, args: list[str]) -> None:
    if sys.stdout.isatty():
        console.rule(f'[bold {ACENTO}]{cmd.icono}  {cmd.clave}[/] [dim]{unir(args)}[/]', align='left', style=ACENTO)
    # -m: el hijo se relanza solo en su venv y ve src/ por PYTHONPATH
    relanzar([sys.executable, '-m', cmd.modulo, *args], env_src())


def cancelar() -> None:
    console.print('[dim]✕ Cancelado.[/]')
    raise typer.Exit(130)


def ejecutar(cmd: Comando, args: list[str]) -> None:
    if '-h' in args or '--help' in args:
        return ayuda(cmd)
    if cmd.asistente and sys.stdin.isatty() and sys.stdout.isatty():
        try:
            asistente(cmd, args)
        except KeyboardInterrupt:  # Ctrl+C en una pregunta; sin esto Click imprime "Aborted!"
            cancelar()
    lanzar(cmd, args)
