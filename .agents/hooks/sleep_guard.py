"""PreToolUse de la shell (Claude Code, Codex y Antigravity): bloquea `sleep` en primer plano (command-output.md).

Un `sleep 60` en primer plano congela al agente sin avanzar y, en un lote, se repite cada vez que espera algo (un
commit con hooks lentos, la CI, la GPU). Lo correcto es lanzar el comando en segundo plano, esperar con un comando
que bloquea hasta la señal real (`gh pr checks --watch`, `git commit` sin `&`) o vigilar con Monitor. Lee el JSON
del evento por stdin. Claude Code y Codex (`tool_input.command`) bloquean con exit 2 y el motivo en stderr;
Antigravity (`toolCall.args.CommandLine`) no documenta exit codes y bloquea con `{"decision": "deny"}` en stdout.
Solo stdlib.
"""

from __future__ import annotations

import json
import re
import sys

# shortcut: un `sleep` dentro de comillas (`bash -c 'sleep 5'`) pasa; parsear la shell si se vuelve común.
# Un `sleep`/`Start-Sleep` al inicio de un comando simple: tras el comienzo, un operador o `do`/`then`/`else`.
SLEEP = re.compile(r'(?:^|[;&|\n(`{]|\b(?:do|then|else)\b)\s*(?:sleep|Start-Sleep)\b', re.IGNORECASE)
REASON = (
    'Blocked by .agents/hooks/sleep_guard.py (command-output.md): no foreground `sleep`. Run the long command in the '
    'background (run_in_background) and wait for its notification, block on the real signal (`gh pr checks <n> '
    '--watch`, the command itself) or watch a condition with Monitor.'
)


def sleeps(command: str) -> bool:
    """Si el comando duerme en primer plano (no si `sleep` solo aparece como texto).

    >>> sleeps('sleep 60; tail -c 1500 out.log'), sleeps('git fetch && sleep 5'), sleeps('Start-Sleep -s 3')
    (True, True, True)
    >>> sleeps('until [ -f x ]; do sleep 2; done'), sleeps('timeout 9 bash -c "sleep 1"')
    (True, False)
    >>> sleeps('git commit -m "fix: sleep guard"'), sleeps('echo sleeping'), sleeps('grep -n sleep a.md')
    (False, False, False)
    """
    return bool(SLEEP.search(command))


def blocked(event: dict) -> bool:
    """El evento duerme en primer plano: Bash de Claude Code (`run_in_background` lo permite), shell de Codex o
    `run_command` de Antigravity.

    >>> blocked({'tool_input': {'command': 'sleep 30'}})
    True
    >>> blocked({'tool_input': {'command': 'sleep 30', 'run_in_background': True}})
    False
    >>> blocked({'tool_input': {'command': ['bash', '-lc', 'sleep 5 && ls']}})
    True
    >>> blocked({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'Start-Sleep 10; dir'}}})
    True
    """
    if 'toolCall' in event:
        return sleeps(str(((event.get('toolCall') or {}).get('args') or {}).get('CommandLine', '')))
    tool_input = event.get('tool_input') or {}
    if tool_input.get('run_in_background'):
        return False
    command = tool_input.get('command', '')
    if isinstance(command, list):
        command = ' '.join(str(part) for part in command[-1:])
    return sleeps(str(command))


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or '{}')
    except json.JSONDecodeError:
        return 0
    if not blocked(event):
        return 0
    if 'toolCall' in event:
        print(json.dumps({'decision': 'deny', 'reason': REASON}))
        return 0
    print(REASON, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
