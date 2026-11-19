"""La app de Typer, armada desde comandos.REGISTRO: la 1.ª palabra de la clave es el grupo."""

from __future__ import annotations

import sys

import typer

from content_studio.cli.commands import GROUPS, REGISTRY, Command
from content_studio.cli.flow import execute
from content_studio.cli.menu import menu
from content_studio.cli.widgets import console
from content_studio.common.process import console_utf8

# Los flags pasan tal cual al parser del script: Typer no los interpreta.
STEP = dict(context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}, add_help_option=False)
app = typer.Typer(
    help='Audio local para videos: narración y música. Sin argumentos abre el menú.',
    add_completion=False,
    rich_markup_mode='rich',
)


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        if sys.stdin.isatty() and sys.stdout.isatty():
            menu()
        else:
            console.print(ctx.get_help())


def _step(cmd: Command):
    def correr(ctx: typer.Context) -> None:
        execute(cmd, ctx.args)

    return correr


def register(destination: typer.Typer, commands: list[Command]) -> None:
    groups: dict[str, typer.Typer] = {}
    for cmd in commands:
        *group, name = cmd.key.split()
        parent = destination
        if group:
            if group[0] not in groups:
                groups[group[0]] = typer.Typer(help=GROUPS[group[0]], no_args_is_help=True)
                destination.add_typer(groups[group[0]], name=group[0])
            parent = groups[group[0]]
        parent.command(name=name, help=cmd.help, **STEP)(_step(cmd))


register(app, REGISTRY)


def main() -> None:
    console_utf8()
    try:
        app()
    except KeyboardInterrupt:
        console.print('\n[dim]Cancelado.[/]')
        sys.exit(130)
