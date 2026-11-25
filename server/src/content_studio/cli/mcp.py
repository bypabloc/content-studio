"""`studio mcp` (spec 029): el servidor MCP por stdio, y `studio mcp config`, el fragmento de cada cliente."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import Any

from content_studio.mcp_server.config import CLIENTS, fragment, launch_command


def add_parser(sub: Any, db_flag: Callable[[], argparse.ArgumentParser]) -> None:
    """Registra `studio mcp` (el protocolo por stdio) y `studio mcp config --client <c>`."""
    mcp = sub.add_parser('mcp', parents=[db_flag()], help='MCP server over stdio for LLM clients and agents (spec 029)')
    commands = mcp.add_subparsers(dest='mcp_command')
    config = commands.add_parser('config', help='print the MCP config fragment of a client (spec 029)')
    config.add_argument('--client', required=True, choices=CLIENTS, help='client to configure')


def dispatch(args: argparse.Namespace) -> int:
    """Imprime el fragmento, o arranca el bridge; el SDK `mcp` se importa solo al arrancarlo."""
    if getattr(args, 'mcp_command', None) == 'config':
        print(fragment(args.client, launch_command()))
        return 0
    from content_studio.mcp_server.bridge import run_stdio

    try:
        run_stdio(args.db)
    except ImportError as error:
        print(f'studio mcp needs the mcp package: {error}', file=sys.stderr)
        return 2
    return 0
