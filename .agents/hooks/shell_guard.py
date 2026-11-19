"""PreToolUse de la shell (Claude Code, Codex y Antigravity): bloquea `sleep` en primer plano y todo uso de WSL.

* `sleep` (command-output.md): congela al agente sin avanzar. Se espera en segundo plano, con un comando que bloquea
  hasta la señal real (`gh pr checks --watch`) o con Monitor.
* `wsl` (command-output.md): WSL es otra instancia que al usuario no le interesa. Un fallo que solo da la CI (Linux) se
  diagnostica con `gh run view <id> --log-failed` y se valida con el push, nunca instalando ni corriendo nada en WSL.

Lee el JSON del evento por stdin. Claude Code y Codex (`tool_input.command`) bloquean con exit 2 y el motivo en
stderr; Antigravity (`toolCall.args.CommandLine`) no documenta exit codes y bloquea con `{"decision": "deny"}` en
stdout. Solo stdlib.
"""

from __future__ import annotations

import json
import re
import sys

# shortcut: un comando dentro de comillas (`bash -c 'sleep 5'`) pasa; parsear la shell si se vuelve común.
# Inicio de un comando simple: el comienzo, un operador o `do`/`then`/`else`, y variables de entorno delante.
# Sin la comilla invertida: en un mensaje de commit es markdown, no una sustitución.
START = r'(?:^|[;&|\n(]|\b(?:do|then|else)\b)\s*(?:\w+=\S*\s+)*'
RULES = [
    (
        re.compile(START + r'(?:sleep|Start-Sleep)\b', re.IGNORECASE),
        'Blocked by .agents/hooks/shell_guard.py (command-output.md): no foreground `sleep`. Run the long command in '
        'the background (run_in_background) and wait for its notification, block on the real signal (`gh pr checks '
        '<n> --watch`, the command itself) or watch a condition with Monitor.',
    ),
    (
        re.compile(START + r'wsl(?:\.exe)?\b', re.IGNORECASE),
        'Blocked by .agents/hooks/shell_guard.py (command-output.md): nothing runs in WSL, not tests, installs nor CI '
        'reproductions. Read a Linux-only CI failure with `gh run view <id> --log-failed`, fix it here and validate '
        'with the push; leave a PENDING note if it cannot be checked before.',
    ),
]


def reason(command: str) -> str | None:
    """El motivo del bloqueo, o None si el comando no duerme en primer plano ni usa WSL.

    >>> [bool(reason(c)) for c in ('sleep 60; tail out.log', 'git fetch && sleep 5', 'Start-Sleep -s 3')]
    [True, True, True]
    >>> [bool(reason(c)) for c in ('until [ -f x ]; do sleep 2; done', 'timeout 9 bash -c "sleep 1"')]
    [True, False]
    >>> [bool(reason(c)) for c in ("wsl -e bash -lc 'uv run pytest'", 'MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- ls')]
    [True, True]
    >>> [bool(reason(c)) for c in ('wsl.exe -l -v', 'cd x && wsl --shutdown')]
    [True, True]
    >>> [bool(reason(c)) for c in ('git commit -m "fix: sleep y wsl"', 'grep -n wsl a.md', 'echo sleeping')]
    [False, False, False]
    >>> bool(reason('git commit -m "docs: nada de `sleep` ni `wsl`"'))
    False
    """
    return next((text for pattern, text in RULES if pattern.search(command)), None)


def check(event: dict) -> str | None:
    """El motivo para el evento: Bash de Claude Code (`run_in_background` permite el `sleep`), shell de Codex o
    `run_command` de Antigravity.

    >>> bool(check({'tool_input': {'command': 'sleep 30'}}))
    True
    >>> check({'tool_input': {'command': 'sleep 30', 'run_in_background': True}}) is None
    True
    >>> bool(check({'tool_input': {'command': 'wsl -e ls', 'run_in_background': True}}))
    True
    >>> bool(check({'tool_input': {'command': ['bash', '-lc', 'sleep 5 && ls']}}))
    True
    >>> bool(check({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'Start-Sleep 10; dir'}}}))
    True
    """
    if 'toolCall' in event:
        return reason(str(((event.get('toolCall') or {}).get('args') or {}).get('CommandLine', '')))
    tool_input = event.get('tool_input') or {}
    command = tool_input.get('command', '')
    if isinstance(command, list):
        command = ' '.join(str(part) for part in command[-1:])
    found = reason(str(command))
    # En segundo plano, un `sleep` no congela al agente; WSL sigue prohibido.
    if found == RULES[0][1] and tool_input.get('run_in_background'):
        return None
    return found


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
