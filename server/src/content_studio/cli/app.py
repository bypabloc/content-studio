"""La app de Typer, armada desde comandos.REGISTRO: la 1.ª palabra de la clave es el grupo."""

from __future__ import annotations

import sys

import typer

from content_studio.cli.comandos import GRUPOS, REGISTRO, Comando
from content_studio.cli.flujo import ejecutar
from content_studio.cli.menu import menu
from content_studio.cli.widgets import console
from content_studio.comun.proceso import consola_utf8

# Los flags pasan tal cual al parser del script: Typer no los interpreta.
PASO = dict(context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}, add_help_option=False)
app = typer.Typer(
    help='Audio local para videos: narración y música. Sin argumentos abre el menú.',
    add_completion=False,
    rich_markup_mode='rich',
)


@app.callback(invoke_without_command=True)
def raiz(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        if sys.stdin.isatty() and sys.stdout.isatty():
            menu()
        else:
            console.print(ctx.get_help())


def _paso(cmd: Comando):
    def correr(ctx: typer.Context) -> None:
        ejecutar(cmd, ctx.args)

    return correr


def registrar(destino: typer.Typer, comandos: list[Comando]) -> None:
    grupos: dict[str, typer.Typer] = {}
    for cmd in comandos:
        *grupo, nombre = cmd.clave.split()
        padre = destino
        if grupo:
            if grupo[0] not in grupos:
                grupos[grupo[0]] = typer.Typer(help=GRUPOS[grupo[0]], no_args_is_help=True)
                destino.add_typer(grupos[grupo[0]], name=grupo[0])
            padre = grupos[grupo[0]]
        padre.command(name=nombre, help=cmd.ayuda, **PASO)(_paso(cmd))


registrar(app, REGISTRO)


def main() -> None:
    consola_utf8()
    try:
        app()
    except KeyboardInterrupt:
        console.print('\n[dim]Cancelado.[/]')
        sys.exit(130)
