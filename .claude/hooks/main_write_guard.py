"""PreToolUse (Write, Edit, NotebookEdit): nada se edita en el checkout principal mientras está en `dev` o `main`.

`dev` y `main` cambian solo por PR (git-workflow.md) y el principal es el checkout que comparten las sesiones: una
edición ahí se mezcla con el trabajo del usuario. Una sesión que trabaja en un worktree apuntó por error a la ruta
del principal (lote 001-017). Lo ignorado por git (`tmp/`, `logs/`, `out/`, el handoff) sí se escribe. Con el
principal en una rama de trabajo, no bloquea (un cambio chico sin worktree). Exit 2 con el motivo en stderr bloquea.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

PROTECTED = {'dev', 'main'}


def _git(cwd: str, *args: str) -> str:
    try:
        r = subprocess.run(['git', '-C', cwd, *args], capture_output=True, text=True, timeout=5)
    except Exception:
        return ''
    return r.stdout.strip() if r.returncode == 0 else ''


def native(path: str) -> str:
    """Una ruta de Git Bash (`/d/x`) como la entiende git de Windows (`D:/x`); las demás, igual.

    >>> native('/d/Users/x') == ('D:/Users/x' if os.name == 'nt' else '/d/Users/x'), native('a/b')
    (True, 'a/b')
    """
    return re.sub(r'^/([a-zA-Z])/', lambda m: f'{m.group(1).upper()}:/', path) if os.name == 'nt' else path


def inside(path: str, root: str) -> str | None:
    """La ruta relativa a `root` (con `/` y sus mayúsculas), o None si `path` cae fuera.

    >>> inside('/r/a/B.py', '/r'), inside('/r', '/r'), inside('/r-worktrees/x/a.py', '/r')
    ('a/B.py', '', None)
    """
    p, r = os.path.realpath(path), os.path.realpath(root)
    if os.path.normcase(p) == os.path.normcase(r):
        return ''
    if not os.path.normcase(p).startswith(os.path.normcase(r) + os.sep):
        return None
    return p[len(r) + 1 :].replace(os.sep, '/')


def message(rel: str, branch: str, worktrees: list[str]) -> str:
    """El motivo, con el mismo archivo en el worktree si hay uno solo.

    >>> 'content-studio-worktrees/005/docs/a.md' in message('docs/a.md', 'dev', ['D:/x/content-studio-worktrees/005'])
    True
    >>> all(p in message('a.py', 'main', []) for p in ('Blocked by', 'Why:', 'Instead:'))
    True
    """
    where = (
        f'edit {worktrees[0].rstrip("/")}/{rel}'
        if len(worktrees) == 1
        else 'edit the same path in your worktree (`git worktree list`)'
    )
    return (
        f'Blocked by .claude/hooks/main_write_guard.py: editing `{rel}` in the main checkout, which is on `{branch}`. '
        f'Why: `{branch}` only changes through a PR and the main checkout is shared with the user and other sessions '
        f'(git-workflow.md, worktrees.md). Instead: {where}, or create a worktree from origin/dev '
        '(../content-studio-worktrees/<name>, worktrees.md). Ignored paths such as tmp/ stay writable.'
    )


def check(path: str, cwd: str) -> str | None:
    """El motivo del bloqueo, o None si la edición no toca un archivo versionado del principal en dev o main."""
    common = _git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if not path or not common:
        return None
    main = os.path.dirname(common)
    rel = inside(path if os.path.isabs(path) else os.path.join(cwd, path), main)
    if not rel:
        return None
    branch = _git(main, 'branch', '--show-current')
    if branch not in PROTECTED or _git(main, 'check-ignore', rel):
        return None
    lines = _git(main, 'worktree', 'list', '--porcelain').splitlines()
    roots = [line[len('worktree ') :] for line in lines if line.startswith('worktree ')]
    others = [r for r in roots if inside(r, main) is None]
    return message(rel, branch, others)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = data.get('tool_input') or {}
    path = native(str(tool_input.get('file_path') or tool_input.get('notebook_path') or ''))
    found = check(path, native(data.get('cwd') or os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()))
    if found:
        print(found, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
