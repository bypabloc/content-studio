"""PostToolUse de Bash: tras un `git commit`, recuerda actualizar el PROGRESS.md del handoff de la sesión. No bloquea.

En un lote, el agente encadenaba commits sin anotarlos y, al compactar, retomaba desde un `Next step` viejo
(execute-spec §2.6). El vínculo de la sesión vive en `tmp/handoff/.sessions/<session_id>` del checkout principal.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', Path(__file__).resolve().parents[2]))


def is_commit(command: str) -> bool:
    """Si el comando hace un commit (no un `git commit --help` ni un texto que lo mencione).

    >>> is_commit('cd ../wt && git add -A && git commit -q -F - <<EOF')
    True
    >>> is_commit('git -C ../wt commit -m "x"')
    True
    >>> is_commit('git log --oneline -1'), is_commit('echo "git commit"'), is_commit('git commit --help')
    (False, False, False)
    """
    calls = re.findall(r'(?:^|&&|;|\|\||\n)\s*git\s+(?:-C\s+\S+\s+|-c\s+\S+\s+)*commit\b([^&;\n]*)', command)
    return any('--help' not in args and '--dry-run' not in args for args in calls)


def commit_hash(stdout: str) -> str | None:
    """El hash corto de la salida de git commit (sin -q).

    >>> commit_hash('[chore/003-x 70ff3be] chore: auditoría\\n 2 files changed')
    '70ff3be'
    >>> commit_hash('') is None
    True
    """
    found = re.search(r'^\[[^\]\s]+(?: \([^)]*\))? ([0-9a-f]{7,40})\]', stdout, re.M)
    return found.group(1) if found else None


def main_checkout(root: Path) -> Path:
    """El checkout principal (donde vive tmp/handoff/), también si la sesión corre en un worktree."""
    r = subprocess.run(
        ['git', '-C', str(root), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        capture_output=True,
        text=True,
    )
    return Path(r.stdout.strip()).parent if r.returncode == 0 and r.stdout.strip() else root


def reminder(job: str, progress: str, sha: str | None) -> str | None:
    """El aviso, o None si PROGRESS.md ya cita el hash.

    >>> reminder('lote', 'Done: 001 (abc1234)', 'abc1234') is None
    True
    >>> 'lote/PROGRESS.md' in reminder('lote', 'Done: 001', None)
    True
    """
    if sha and sha in progress:
        return None
    ref = sha or 'the one from `git log -1 --format=%h`'
    return (
        f'[progress] Commit done: update tmp/handoff/{job}/PROGRESS.md now (execute-spec §2.6), in this same '
        f'response: hash {ref} in Done, plus Current, Remaining, ETA and Next step for the next group. '
        'A stale Next step after compaction means redoing work.'
    )


def main() -> None:
    data = json.loads(sys.stdin.read() or '{}')
    if not is_commit(str((data.get('tool_input') or {}).get('command', ''))):
        return
    base = main_checkout(ROOT) / 'tmp/handoff'
    link = base / '.sessions' / str(data.get('session_id', ''))
    if not data.get('session_id') or not link.is_file():
        return
    job = link.read_text(encoding='utf-8').strip()
    progress = base / job / 'PROGRESS.md'
    text = progress.read_text(encoding='utf-8') if progress.is_file() else ''
    response = data.get('tool_response') or {}
    stdout = response.get('stdout', '') if isinstance(response, dict) else str(response)
    note = reminder(job, text, commit_hash(stdout))
    if note:
        out = {'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': note}}
        print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
