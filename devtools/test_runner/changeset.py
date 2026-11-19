"""Archivos sobre los que corre cada etapa, según `--git-mode` (spec 003, D-1).

Git se consulta desde el directorio actual (o `root` en los tests), no desde el checkout del runner: así el pre-commit
ve lo staged del repo donde se hace el commit, también cuando el hook corre dentro de un repo temporal.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

GIT_MODES = ('changed', 'staged', 'unstaged', 'unmerged', 'all')

ORDERS = {
    'changed': ['diff', '--name-only', '--relative', '--diff-filter=ACMR', 'origin/dev'],
    'staged': ['diff', '--cached', '--name-only', '--relative', '--diff-filter=ACMR'],
    'unstaged': ['diff', '--name-only', '--relative', '--diff-filter=ACMR'],
    'unmerged': ['diff', '--name-only', '--relative', '--diff-filter=ACMR', 'origin/dev...HEAD'],
    'all': ['ls-files'],
}


def files(mode: str, explicit: list[Path] | None, root: Path | None = None) -> list[Path]:
    """Lista explícita gana al modo; si no, lo que git reporta para el modo, relativo a `root` (por defecto, cwd)."""
    if explicit is not None:
        return explicit
    base = Path.cwd() if root is None else root
    out = subprocess.run(['git', *ORDERS[mode]], cwd=base, capture_output=True, encoding='utf-8', check=True).stdout
    return [base / name for name in out.splitlines() if name]
