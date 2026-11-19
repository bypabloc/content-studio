"""PreToolUse (Bash): ningún `git worktree add` dentro del repo.

Un worktree dentro del checkout principal hace que la sesión cargue sus `.claude/rules` como reglas anidadas,
duplicadas (en klinikae sumó +45k tokens por compactación). Van en ../content-studio-worktrees/ (worktrees.md).
Exit 2 con el motivo en stderr bloquea el comando. Adaptado de klinikae.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys

OPERATORS = {'&&', '||', ';', '|', '&', '(', ')'}
# Opciones de `git worktree add` que consumen el siguiente token.
VALUED = {'-b', '-B', '--orphan', '--reason'}


def _segments(command: str) -> list[list[str]]:
    """Comandos simples de una línea de shell, separados por sus operadores."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    out: list[list[str]] = [[]]
    for token in tokens:
        if token in OPERATORS:
            out.append([])
        else:
            out[-1].append(token)
    return [s for s in out if s]


def target_inside(command: str, cwd: str, repo: str) -> str | None:
    """Ruta del `git worktree add` de `command` que cae dentro de `repo`, o None.

    >>> target_inside('git worktree add .worktrees/x -b feature/x', '/r', '/r')
    '.worktrees/x'
    >>> target_inside('git worktree add ../r-worktrees/x origin/dev', '/r', '/r') is None
    True
    """
    root = os.path.normcase(os.path.realpath(repo))
    for seg in _segments(command):
        if seg[0] != 'git':
            continue
        base, i = cwd, 1
        while i < len(seg) and seg[i] in ('-C', '-c'):
            if seg[i] == '-C' and i + 1 < len(seg):
                base = os.path.join(base, seg[i + 1])
            i += 2
        if seg[i : i + 2] != ['worktree', 'add']:
            continue
        rest, j = seg[i + 2 :], 0
        while j < len(rest) and rest[j].startswith('-'):
            j += 2 if rest[j] in VALUED else 1
        if j >= len(rest):
            continue
        path = os.path.normcase(os.path.realpath(os.path.join(base, rest[j])))
        if path == root or path.startswith(root + os.sep):
            return rest[j]
    return None


def _roots(cwd: str) -> list[str]:
    """Checkout principal (padre del `.git` común) y el checkout de `cwd`, que puede ser un worktree."""
    try:
        common, top = subprocess.run(
            ['git', '-C', cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.splitlines()
    except Exception:
        return []
    return [os.path.dirname(common), top]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get('tool_input', {}).get('command', '')
    if 'worktree' not in command:
        return
    cwd = data.get('cwd') or os.getcwd()
    target = next((t for root in _roots(cwd) if (t := target_inside(command, cwd, root))), None)
    if target:
        name = os.path.basename(os.path.normpath(target))
        print(
            f'worktree_guard: bloqueado, `{target}` queda dentro del repo y sus reglas se cargarían duplicadas.'
            f' Créalo en ../content-studio-worktrees/{name} (worktrees.md) y corrige la ruta en tu handoff.',
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == '__main__':
    main()
