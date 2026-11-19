"""Ejecutar un comando: directo, o con el asistente que pregunta lo que falta y muestra un resumen editable."""

from __future__ import annotations

import argparse
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

from content_studio import paths
from content_studio.cli.args import a_argv, empty, flags, leer, validate
from content_studio.cli.commands import Command
from content_studio.cli.help_text import show_help
from content_studio.cli.widgets import ACCENT, SEPARATOR, STYLE, ask, console, title
from content_studio.common.process import env_src, join, relaunch


def summary(ap: argparse.ArgumentParser, values: dict, cmd: Command) -> Panel:
    """Resumen editable de los valores del asistente, con el comando equivalente."""
    t = Table(box=None, padding=(0, 2), show_header=False)
    t.add_column(style='bold cyan', no_wrap=True)
    t.add_column(ratio=1)
    for acc in flags(ap):
        given = acc.dest in values and not empty(values[acc.dest])
        v = values[acc.dest] if given else acc.default
        if empty(v):
            continue
        if v is True:
            v = 'sí'
        elif isinstance(v, list):
            v = ' '.join(map(str, v))
        else:
            v = os.path.relpath(v, paths.ROOT) if isinstance(v, Path) and v.is_absolute() else str(v)
        v = v if len(v) < 300 else v[:297] + '…'
        t.add_row(
            Text(acc.option_strings[0], style='bold cyan' if given else 'dim'),
            Text(v, style='green') if given else Text.assemble((v, 'dim'), ('  por defecto', 'dim italic')),
        )
    command = join(['python', 'cli.py', *cmd.key.split(), *a_argv(ap, values)])
    return Panel(
        Group(t, Text(''), Text('$ ' + command, style='dim')),
        title=f'{cmd.icon}  [bold]{cmd.key}[/]',
        title_align='left',
        border_style=ACCENT,
        padding=(1, 2),
    )


def _obligatorios(ap: argparse.ArgumentParser, values: dict, cat: dict) -> None:
    """Pregunta los obligatorios que faltan, en el orden del parser. Un grupo excluyente es una elección previa."""
    for acc in flags(ap):
        group = next((g for g in ap._mutually_exclusive_groups if g.required and acc in g._group_actions), None)
        if group:
            if any(values.get(a.dest) is not None for a in group._group_actions):
                continue
            acc = questionary.select(
                '¿De dónde sale el contenido?',
                style=STYLE,
                instruction='(↑↓ · enter)',
                choices=[Choice(title(a.option_strings[0], a.help or ''), value=a) for a in group._group_actions],
            ).unsafe_ask()
        elif not acc.required or values.get(acc.dest) is not None:
            continue
        values[acc.dest] = ask(acc, cat, None)


def _editar(ap: argparse.ArgumentParser, values: dict, cat: dict) -> None:
    """Elige una opción y la vuelve a preguntar. --file reemplaza a --text y viceversa."""
    options = []
    for acc in flags(ap):
        v = values.get(acc.dest)
        if empty(v):
            state = acc.help or ''
        else:
            state = '✓ ' + (' '.join(map(str, v)) if isinstance(v, list) else 'sí' if v is True else str(v))
        options.append(Choice(title(acc.option_strings[0], state[:90]), value=acc))
    acc = questionary.select(
        '¿Qué opción?',
        choices=[*options, Separator(SEPARATOR), Choice('↩  Volver', None)],
        style=STYLE,
        instruction='(↑↓ · enter)',
    ).unsafe_ask()
    if acc is None:
        return
    values[acc.dest] = ask(acc, cat, values.get(acc.dest))
    for g in ap._mutually_exclusive_groups:
        if acc in g._group_actions and values[acc.dest] is not None:
            for other in g._group_actions:
                if other is not acc:
                    values.pop(other.dest, None)


def assistant(cmd: Command, args: list[str], force: bool = False) -> None:
    """Asistente de un comando: completa los flags que faltan y ejecuta; sin TTY no pregunta."""
    mod = cmd.load()
    ap = mod.build_parser()
    if not force and validate(mod, args) is None:
        lanzar(cmd, args)
    values, notices = leer(mod.build_parser(), args)
    for notice in notices:
        console.print(f'[yellow]⚠ {notice}[/]')
    cat = cmd.catalog(mod)
    console.print(f'\n{cmd.icon}  [bold]{cmd.title}[/]  [dim]{cmd.desc}[/]\n')
    _obligatorios(ap, values, cat)
    while True:  # resumen editable hasta ejecutar, redibujado en su lugar
        console.clear()
        console.print(summary(ap, values, cmd))
        argv = a_argv(ap, values)
        error = validate(mod, argv)
        if error:
            console.print(f'[red]✗ {error}[/]')
        action = questionary.select(
            '¿Qué hacemos?',
            style=STYLE,
            instruction='(↑↓ · enter)',
            choices=[
                Choice('▶  Ejecutar', 'execute', disabled='corrige el error' if error else None),
                Choice('✎  Agregar o cambiar una opción', 'editar'),
                Choice('✕  Cancelar', 'cancel'),
            ],
        ).unsafe_ask()
        if action == 'execute':
            lanzar(cmd, argv)
        if action == 'cancel':
            cancel()
        _editar(ap, values, cat)


def lanzar(cmd: Command, args: list[str]) -> None:
    """Ejecuta el comando en su venv, en un proceso hijo."""
    if sys.stdout.isatty():
        console.rule(f'[bold {ACCENT}]{cmd.icon}  {cmd.key}[/] [dim]{join(args)}[/]', align='left', style=ACCENT)
    # -m: el hijo se relanza solo en su venv y ve src/ por PYTHONPATH
    relaunch([sys.executable, '-m', cmd.module, *args], env_src())


def cancel() -> None:
    """Cancela el asistente (exit 130)."""
    console.print('[dim]✕ Cancelado.[/]')
    raise typer.Exit(130)


def execute(cmd: Command, args: list[str]) -> None:
    """Ejecuta un comando: su ayuda con -h, o el asistente si hace falta."""
    if '-h' in args or '--help' in args:
        return show_help(cmd)
    if cmd.assistant and sys.stdin.isatty() and sys.stdout.isatty():
        try:
            assistant(cmd, args)
        except KeyboardInterrupt:  # Ctrl+C en una pregunta; sin esto Click imprime "Aborted!"
            cancel()
    lanzar(cmd, args)
