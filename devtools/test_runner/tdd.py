"""Etapa `tdd`: corre los tests efímeros de server/tests/tdd/ y devtools/tests/tdd/ (spec 003, D-5).

Sale con 1 si alguno falla. Sin esas carpetas, pasa sin correr pytest. `guard-tdd` impide que queden en el push.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import paths
from .guard_tdd import TDD_DIRS


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """`files` no cambia el resultado: se corre todo lo que haya en tdd/."""
    folders = [d for d in TDD_DIRS if (root / d).is_dir()]
    if not folders:
        return {'stage': 'tdd', 'status': 'pass', 'detail': ''}
    command = ['uv', 'run', '--project', str(paths.ROOT), 'pytest', '-q', *folders]
    done = subprocess.run(command, cwd=root, capture_output=True, encoding='utf-8', errors='replace')
    return {
        'stage': 'tdd',
        'status': 'pass' if done.returncode == 0 else 'fail',
        'detail': '' if done.returncode == 0 else (done.stdout + done.stderr).strip()[-2000:],
    }
