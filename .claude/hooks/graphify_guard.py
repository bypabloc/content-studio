"""PreToolUse (Bash, Grep, Glob, Read): sugiere graphify al buscar o leer código; calla en las excepciones.

Uso: graphify_guard.py search|read (stdin: payload de la tool). Siempre exit 0: es una sugerencia
(additionalContext), nunca un bloqueo. Regla: .claude/rules/graphify.md. Adaptado de klinikae.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SEARCH_TOKENS = ('rg ', 'grep', 'find ', 'fd ', 'ag ', 'ack ')
# Datos (server/data/narration/, server/data/music/), docs y salidas: el grafo no los indexa o no aportan nodos.
EXCEPTION_PREFIXES = (
    'tmp/', 'out/', 'logs/', 'models/', 'docs/', 'server/data/narration/', 'server/data/music/', 'graphify-out/',
    '.claude/', '.agents/',
    'server/tests/fixtures/', '.venv', '~/.claude', '/tmp/',
)  # fmt: skip
EXCEPTION_SUFFIXES = ('.log', '.json', '.lock', '.png', '.md', '.txt', '.wav', '.toml', '.yml')
CODE_PREFIXES = ('server/src/', 'server/tests/', 'devtools/', 'tests/')
SUGGESTION = (
    'Tip (graphify.md): to locate code, see who uses it or what breaks a change, '
    '`graphify query|explain|affected` answers with fewer tokens than grep or a blind read. '
    'If you already oriented yourself with the graph, carry on.'
)


def _relative(path: str, root: str) -> str:
    path = path.strip('\'"').replace('\\', '/')
    prefix = root.replace('\\', '/').rstrip('/') + '/'
    return path[len(prefix) :] if root and path.lower().startswith(prefix.lower()) else path.removeprefix('./')


def is_exception(path: str) -> bool:
    """True si la ruta es un archivo que el grafo no indexa.

    >>> is_exception('server/data/narration/README.md'), is_exception('server/src/content_studio/paths.py')
    (True, False)
    """
    return (
        path.startswith(EXCEPTION_PREFIXES)
        or path.rsplit('/', 1)[-1].startswith('.env')
        or path.endswith(EXCEPTION_SUFFIXES)
        or any(f'/{p}' in path for p in ('tmp/', 'node_modules/', '.venv'))
    )


def should_suggest_bash(command: str, root: str) -> bool:
    """True si un comando Bash de búsqueda apunta a código (o no acota a una excepción). Un grep tras una tubería
    filtra la salida de otro comando: no es una búsqueda en el código.

    >>> should_suggest_bash('git log | grep -v x', ''), should_suggest_bash('grep -rn relanzar server/src/', '')
    (False, True)
    """
    command = ' '.join(seg.split('|')[0] for seg in re.split(r'&&|\|\||;|\n', command))
    if not any(token in command for token in SEARCH_TOKENS):
        return False
    words = [_relative(w, root) for w in re.split(r'\s+', command)]
    paths = [w for w in words if '/' in w or w.startswith('.') or w.endswith(EXCEPTION_SUFFIXES)]
    if any(p.startswith(CODE_PREFIXES) and not is_exception(p) for p in paths):
        return True
    return not any(is_exception(p) for p in paths)


def should_suggest(mode: str, tool_input: dict, root: str) -> bool:
    """Decide si emitir la sugerencia para el payload de la tool."""
    if 'command' in tool_input:
        return should_suggest_bash(tool_input['command'], root)
    if mode == 'search':
        target = _relative(tool_input.get('path') or '', root)
        glob = tool_input.get('glob') or ''
        return not (target and is_exception(target)) and not (glob and is_exception(glob))
    target = _relative(tool_input.get('file_path') or tool_input.get('pattern') or '', root)
    return target.endswith('.py') and not is_exception(target)


def main() -> int:
    root = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    if not (Path(root) / 'graphify-out' / 'graph.json').exists():
        return 0
    try:
        tool_input = json.loads(sys.stdin.read()).get('tool_input') or {}
        if not should_suggest(sys.argv[1] if len(sys.argv) > 1 else 'search', tool_input, root):
            return 0
    except (ValueError, AttributeError, TypeError):
        return 0
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': SUGGESTION}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
