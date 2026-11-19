"""Etapa `typecheck`: mypy sobre server/src y devtools (spec 003, D-4).

La configuración vive en pyproject.toml ([tool.mypy]). El caché va a tmp/test-runner/ para no ensuciar la raíz. Sale
con 1 si mypy encuentra errores; el detalle es la salida de mypy.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import paths

TARGETS = ['server/src', 'devtools']


def run(files: list[Path], root: Path = paths.ROOT, targets: list[str] = TARGETS) -> dict:
    """`files` no cambia el resultado: mypy mira los targets completos, como en la CI."""
    command = [
        'uv',
        'run',
        '--project',
        str(paths.ROOT),
        'mypy',
        '--cache-dir',
        str(root / 'tmp/test-runner/.mypy_cache'),
        *targets,
    ]
    done = subprocess.run(command, cwd=root, capture_output=True, encoding='utf-8', errors='replace')
    return {
        'stage': 'typecheck',
        'status': 'pass' if done.returncode == 0 else 'fail',
        'detail': done.stdout.strip(),
    }
