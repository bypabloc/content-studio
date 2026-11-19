"""Etapas `client-*` del test-runner (spec 005, D-9): cada una corre un script de client/ con bun.

El resultado es el dict de la etapa; si el script falla, `detail` es su salida (el log va al terminal).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import paths


def _script(stage: str, script: str, root: Path) -> dict:
    done = subprocess.run(
        ['bun', 'run', script],
        cwd=root / 'client',
        capture_output=True,
        encoding='utf-8',
        errors='replace',
    )
    ok = done.returncode == 0
    return {
        'stage': stage,
        'status': 'pass' if ok else 'fail',
        'detail': '' if ok else (done.stdout + done.stderr).strip(),
    }


def lint(files: list[Path], root: Path = paths.ROOT) -> dict:
    """`files` no cambia el resultado: oxlint mira src y tests completos, como en la CI."""
    return _script('client-lint', 'lint', root)


def typecheck(files: list[Path], root: Path = paths.ROOT) -> dict:
    """`tsc --noEmit` sobre client/tsconfig.json."""
    return _script('client-typecheck', 'typecheck', root)


def unit(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Vitest con cobertura por archivo (el umbral vive en client/vite.config.ts)."""
    return _script('client-unit', 'test', root)
