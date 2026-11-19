"""Archivos sobre los que corre cada etapa, según `--git-mode` (spec 003, D-1)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import paths

GIT_MODES = ('changed', 'staged', 'unstaged', 'unmerged', 'all')

ORDERS = {
    'changed': ['diff', '--name-only', '--diff-filter=ACMR', 'origin/dev'],
    'staged': ['diff', '--cached', '--name-only', '--diff-filter=ACMR'],
    'unstaged': ['diff', '--name-only', '--diff-filter=ACMR'],
    'unmerged': ['diff', '--name-only', '--diff-filter=ACMR', 'origin/dev...HEAD'],
    'all': ['ls-files'],
}


def files(mode: str, explicit: list[Path] | None, root: Path = paths.ROOT) -> list[Path]:
    """Lista explícita gana al modo; si no, lo que git reporta para el modo, relativo a `root`."""
    if explicit is not None:
        return explicit
    out = subprocess.run(['git', *ORDERS[mode]], cwd=root, capture_output=True, encoding='utf-8', check=True).stdout
    return [root / name for name in out.splitlines() if name]
