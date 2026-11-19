"""Checkout principal desde cualquier worktree (spec 004, D-3): la carpeta que contiene el .git común."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main_checkout(start: Path) -> Path:
    """Checkout principal, donde vive el candado de la GPU que comparten todos los worktrees."""
    common = subprocess.run(
        ['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        cwd=start,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(common).parent
