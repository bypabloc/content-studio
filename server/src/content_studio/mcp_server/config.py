"""Configuración de cada cliente MCP (spec 029, 02 §3 y AC-9): el fragmento que arranca `studio mcp`, sin token.

Solo stdlib: la CLI lo importa sin el SDK `mcp` ni el venv de los motores.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Literal, get_args

from content_studio import paths

ClientName = Literal['claude-code', 'codex', 'vscode', 'cursor', 'claude-desktop', 'lm-studio', 'jan', 'anythingllm']
CLIENTS: tuple[str, ...] = get_args(ClientName)
SERVER_NAME = 'content-studio'


def launch_command() -> list[str]:
    """El comando que arranca `studio mcp`: el `studio` de la instalación, o `uv run` sobre el checkout."""
    if os.environ.get('CONTENT_STUDIO_MODE') == 'installed':
        script = 'studio.exe' if sys.platform == 'win32' else 'studio'
        return [str(Path(sys.executable).with_name(script)), 'mcp']
    uv = shutil.which('uv') or 'uv'
    return [uv, 'run', '--project', str(paths.ROOT / 'server'), 'studio', 'mcp']


def fragment(client: str, command: list[str]) -> str:
    """El fragmento de `client` que arranca `command` (termina en `mcp`): JSON, o TOML para Codex."""
    if client == 'codex':
        return f'[mcp_servers.{SERVER_NAME}]\ncommand = {json.dumps(command[0])}\nargs = {json.dumps(command[1:])}\n'
    entry: dict[str, object] = {'command': command[0], 'args': command[1:]}
    if client == 'vscode':
        return json.dumps({'servers': {SERVER_NAME: {'type': 'stdio', **entry}}}, indent=2) + '\n'
    return json.dumps({'mcpServers': {SERVER_NAME: entry}}, indent=2) + '\n'
