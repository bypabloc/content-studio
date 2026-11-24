"""Checkout principal desde cualquier worktree (spec 004, D-3): la carpeta que contiene el .git común."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from content_studio import paths


def main_checkout(start: Path) -> Path:
    """Checkout principal, donde vive el candado de la GPU que comparten todos los worktrees.

    La app instalada no es un repo de git (spec 022): su candado vive en la carpeta de datos.
    """
    if os.environ.get('CONTENT_STUDIO_MODE') == 'installed':
        return paths.data_dir()
    common = subprocess.run(
        ['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        cwd=start,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(common).parent
