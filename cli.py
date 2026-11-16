#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["typer>=0.29"]
# ///
"""Punto de entrada único: python cli.py <herramienta> <comando> [flags del script].

    python cli.py narration tts --modelo qwen-0.6b --estilo experta --texto "..."
    python cli.py narration grabar --listar
    python cli.py music --modelo acestep --estilo lofi-chill --duracion 30

Los flags pasan tal cual al script de cada herramienta, que sigue relanzándose en su venv.
`--help` después del comando muestra la ayuda del script. Si typer no está instalado,
el CLI se relanza con `uv run --script` (uv lee las dependencias del bloque de arriba).
"""

import os
import sys
from pathlib import Path

try:
    import typer
except ImportError:
    try:
        os.execvp('uv', ['uv', 'run', '--quiet', '--script', __file__, *sys.argv[1:]])
    except FileNotFoundError:
        sys.exit('Falta uv (o instala typer en este python). Ver "Requisitos" en AGENTS.md.')

RAIZ = Path(__file__).resolve().parent
# Comandos de paso: aceptan cualquier flag y dejan --help al script.
PASO = dict(context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}, add_help_option=False)

app = typer.Typer(help='Audio local para videos: narración y música.', no_args_is_help=True, add_completion=False)
narration = typer.Typer(help='Narración TTS clonando una voz (narration/README.md).', no_args_is_help=True)
app.add_typer(narration, name='narration')


def lanzar(script: str, args: list[str]) -> None:
    os.execv(sys.executable, [sys.executable, str(RAIZ / script), *args])


@narration.command(**PASO)
def tts(ctx: typer.Context) -> None:
    """Genera narración (narration/tts.py)."""
    lanzar('narration/tts.py', ctx.args)


@narration.command(**PASO)
def grabar(ctx: typer.Context) -> None:
    """Graba las voces de referencia (narration/grabar.py)."""
    lanzar('narration/grabar.py', ctx.args)


@app.command(**PASO)
def music(ctx: typer.Context) -> None:
    """Genera música instrumental (music/musica.py, music/README.md)."""
    lanzar('music/musica.py', ctx.args)


if __name__ == '__main__':
    app()
