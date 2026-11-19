"""Etapa `guard-tdd`: falla si queda algún test efímero en tdd/ (spec 003, D-5).

Los tests de tdd/ sirven para razonar una pieza antes de su spec; no pueden llegar a `dev`. El pre-push llama a esta
etapa; la etapa `tdd` los corre (ver tdd.py).
"""

from __future__ import annotations

from pathlib import Path

from .. import paths

TDD_DIRS = ['server/tests/tdd', 'devtools/tests/tdd']


def leftovers(root: Path) -> list[str]:
    """Tests `test_*.py` que quedan en las carpetas tdd/, relativos a la raíz."""
    return sorted(p.relative_to(root).as_posix() for d in TDD_DIRS for p in (root / d).rglob('test_*.py'))


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """`files` no cambia el resultado: basta que exista un test efímero."""
    found = leftovers(root)
    return {
        'stage': 'guard-tdd',
        'status': 'fail' if found else 'pass',
        'detail': '\n'.join(f'{name}: convert it into a spec test or delete it before the push' for name in found),
    }
