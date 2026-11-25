"""Spec 029, fase 2: cada cliente (AC-9) recibe un fragmento que se parsea, con `studio mcp` y sin token."""

import json
import tomllib

import pytest

from content_studio.mcp_server import config

CLIENTS = ('claude-code', 'codex', 'vscode', 'cursor', 'claude-desktop', 'lm-studio', 'jan', 'anythingllm')
COMMAND = ['C:/Program Files/Content Studio/studio.exe', 'mcp']
TOKEN = 'token-secreto-de-prueba'


@pytest.mark.parametrize('client', CLIENTS)
def test_ac9_valid_fragment_per_client(client):
    text = config.fragment(client, COMMAND)
    if client == 'codex':
        entry = tomllib.loads(text)['mcp_servers']['content-studio']
    else:
        data = json.loads(text)
        entry = (data['servers'] if client == 'vscode' else data['mcpServers'])['content-studio']
    assert entry['command'] == COMMAND[0]
    assert entry['args'] == ['mcp']
    assert TOKEN not in text
