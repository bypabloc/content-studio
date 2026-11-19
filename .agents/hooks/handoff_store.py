"""Lectura del handoff en disco: qué trabajo tiene cada sesión, su PROGRESS.md, la spec que le toca y el checkout
principal que guarda tmp/handoff/ (compartido por todos los worktrees). Solo lee; los mensajes y las decisiones de
los hooks viven en session_handoff.py.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from handoff_text import progress_fields

SAFE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
SPEC_NUMBER = re.compile(r'(?:^|/)(\d{2,3}(?:\.\d+)?)-')


def handoff_dir(root: Path) -> Path:
    return root / 'tmp/handoff'


def spec_folder(root: Path, name: str) -> str | None:
    """Carpeta de docs/specs/ cuyo número coincide con el del trabajo o la rama."""
    match = SPEC_NUMBER.search(name)
    if not match:
        return None
    prefix = f'{match.group(1)}-'
    specs = root / 'docs/specs'
    for candidate in sorted([*specs.glob(f'{prefix}*'), *specs.glob(f'*/{prefix}*')]):
        if candidate.is_dir():
            return candidate.relative_to(root).as_posix()
    return None


def current_work(root: Path, session_id: str, branch: str) -> str | None:
    """Trabajo de la sesión: su vínculo o, si no hay, el que coincide con el número de la rama."""
    base = handoff_dir(root)
    if session_id and SAFE_NAME.match(session_id):
        link = base / '.sessions' / session_id
        if link.is_file():
            name = link.read_text(encoding='utf-8').strip()
            if SAFE_NAME.match(name) and (base / name).is_dir():
                return name
    match = SPEC_NUMBER.search(branch)
    if match and base.is_dir():
        for folder in sorted(base.glob(f'{match.group(1)}-*')):
            if folder.is_dir():
                return folder.name
    return None


def read_progress(folder: Path) -> str:
    progress = folder / 'PROGRESS.md'
    return progress.read_text(encoding='utf-8', errors='replace') if progress.is_file() else ''


def status_of(store: Path, session_id: str, branch: str) -> dict[str, str]:
    """Estado del trabajo vinculado para la banda y el spinner del mod; vacío sin trabajo."""
    work = current_work(store, session_id, branch)
    return {'work': work, **progress_fields(read_progress(handoff_dir(store) / work))} if work else {}


def active_works(root: Path) -> list[tuple[str, str]]:
    """Trabajos con carpeta en tmp/handoff/ y el siguiente paso de su PROGRESS.md."""
    base = handoff_dir(root)
    if not base.is_dir():
        return []
    folders = sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith('.'))
    return [(f.name, progress_fields(read_progress(f)).get('next_step', '')[:160]) for f in folders]


def git(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=False)
    except OSError:
        return ''
    return result.stdout.strip()


def main_checkout(cwd: Path) -> Path | None:
    """Checkout principal del repo de `cwd`, también desde un worktree (padre del `.git` común); None fuera de git."""
    common = git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if not common:
        return None
    path = Path(common)
    return path.parent if path.name == '.git' else Path(git(cwd, 'rev-parse', '--show-toplevel') or cwd)
