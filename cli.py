#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["typer>=0.29", "rich>=14", "questionary>=2.1", "fastapi>=0.162.5", "uvicorn>=0.54.0"]
# ///
"""Punto de entrada único: python cli.py [<herramienta> <comando> [flags]]. El CLI vive en server/src/content_studio.

    python cli.py                                   # menú interactivo
    python cli.py narration tts                     # asistente: pregunta lo que falte
    python cli.py narration tts --model qwen-0.6b --text "..."   # completo: se ejecuta directo
    python cli.py music --model acestep --style lofi-chill

Si este python no tiene las dependencias, el CLI se relanza con `uv run --script` (las lee del bloque de arriba).
"""

import sys
from pathlib import Path

if (_SRC := str(Path(__file__).resolve().parent / 'server' / 'src')) not in sys.path:
    sys.path.insert(0, _SRC)
from content_studio.common.process import relaunch  # noqa: E402  (solo stdlib)

try:
    for _dep in ('typer', 'rich', 'questionary'):
        __import__(_dep)
except ImportError:
    try:
        relaunch(['uv', 'run', '--quiet', '--script', __file__, *sys.argv[1:]])
    except FileNotFoundError:
        sys.exit('Falta uv (o instala typer, rich y questionary en este python). Ver "Requisitos" en AGENTS.md.')

if __name__ == '__main__':
    from content_studio.cli.app import main

    main()
