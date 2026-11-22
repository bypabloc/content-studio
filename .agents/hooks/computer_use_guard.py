"""PreToolUse (Claude Code, Codex y Antigravity): bloquea Computer Use, el control del escritorio (spec 024).

Computer Use abría binarios viejos, esperaba aprobaciones que vencían y tomaba el mouse y el teclado del usuario. La
app se verifica con `python -m devtools app-check run`: Playwright por CDP contra el WebView2 real, sin tocar el
escritorio (verify-before-claiming-done.md).

Se bloquea por nombre (las herramientas MCP de control del escritorio) y por contenido: en Codex, Computer Use es
código que importa `@oai/sky` dentro de `mcp__node_repl__js`, o de `exec`/`js` en modo código. Claude Code y Codex
bloquean con exit 2 y el motivo en stderr; Antigravity, con `{"decision": "deny"}` en stdout. Solo stdlib.
"""

from __future__ import annotations

import json
import re
import sys

# Herramientas que solo controlan el escritorio: Claude Code (app y sesión remota) y Antigravity si agrega una.
TOOLS = re.compile(r'^mcp__computer-use__|^mcp__remote-devices__computer|^computer', re.IGNORECASE)
# Herramientas que corren código: el código decide si es Computer Use.
CODE_TOOLS = {'mcp__node_repl__js', 'js', 'exec'}
CODE = re.compile(r'@oai/sky|\bsky\.\w+\(')
MESSAGE = (
    'Blocked by .agents/hooks/computer_use_guard.py: Computer Use (desktop control). Why: it opens stale binaries, '
    "waits for approvals that time out and takes the user's mouse and keyboard; it is forbidden in this repo "
    '(verify-before-claiming-done.md). Instead: python -m devtools app-check run [--scenario=<name>] '
    "[--data=temp|real], which drives the app's real WebView2 with Playwright over CDP and leaves screenshots in "
    'tmp/app-check/<run>/shots/.'
)


def reason(tool: str, arguments: object) -> str | None:
    """El motivo del bloqueo, o None si la herramienta no controla el escritorio.

    >>> [bool(reason(t, {})) for t in ('mcp__computer-use__screenshot', 'mcp__remote-devices__computer_click')]
    [True, True]
    >>> bool(reason('mcp__node_repl__js', {'code': 'await import("@oai/sky")'}))
    True
    >>> bool(reason('exec', {'code': 'await tools.mcp__node_repl__js({code: "await sky.list_apps()"})'}))
    True
    >>> [reason(t, a) for t, a in (('mcp__node_repl__js', {'code': '1'}), ('exec', {'code': 'text("sky")'}))]
    [None, None]
    >>> reason('Bash', {'command': 'echo "sky.list_apps()"'}) is None
    True
    """
    if TOOLS.search(tool):
        return MESSAGE
    if tool in CODE_TOOLS and CODE.search(json.dumps(arguments)):
        return MESSAGE
    return None


def check(event: dict) -> str | None:
    """El motivo para el evento de Claude Code o Codex (`tool_name`) o de Antigravity (`toolCall`).

    >>> bool(check({'tool_name': 'mcp__computer-use__left_click', 'tool_input': {}}))
    True
    >>> bool(check({'toolCall': {'name': 'computer_click', 'args': {}}}))
    True
    >>> check({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git status'}}}) is None
    True
    """
    if 'toolCall' in event:
        call = event.get('toolCall') or {}
        return reason(str(call.get('name', '')), call.get('args') or {})
    return reason(str(event.get('tool_name', '')), event.get('tool_input') or {})


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or '{}')
    except json.JSONDecodeError:
        return 0
    found = check(event)
    if not found:
        return 0
    if 'toolCall' in event:
        print(json.dumps({'decision': 'deny', 'reason': found}))
        return 0
    print(found, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
