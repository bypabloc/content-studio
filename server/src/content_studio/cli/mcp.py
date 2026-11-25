"""`studio mcp` (spec 029): el servidor MCP por stdio para Claude Code, Codex y los demás clientes locales."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import Any


def add_parser(sub: Any, db_flag: Callable[[], argparse.ArgumentParser]) -> None:
    """Registra `studio mcp`: el protocolo por stdio, sin más opciones."""
    sub.add_parser('mcp', parents=[db_flag()], help='MCP server over stdio for LLM clients and agents (spec 029)')


def dispatch(args: argparse.Namespace) -> int:
    """Arranca el bridge; el SDK `mcp` se importa solo aquí. Sin SDK, sale con 2 y lo dice por stderr."""
    from content_studio.mcp_server.bridge import run_stdio

    try:
        run_stdio(args.db)
    except ImportError as error:
        print(f'studio mcp needs the mcp package: {error}', file=sys.stderr)
        return 2
    return 0
