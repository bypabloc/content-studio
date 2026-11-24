"""Etapa `lint`: ruff check y ruff format --check sobre los `.py` del changeset (spec 003, D-1)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import paths

ORDERS = (['check'], ['format', '--check'])


def _arg(path: Path) -> str:
    """Ruta relativa a la raíz con barras normales: así ruff aplica los per-file-ignores en Windows."""
    try:
        return path.relative_to(paths.ROOT).as_posix()
    except ValueError:
        return str(path)


def run(files: list[Path]) -> dict:
    """Un dict `{"stage", "status", "detail"}`; `pass` sin `.py` que revisar."""
    py = [_arg(f) for f in files if f.suffix == '.py']
    problems = []
    for order in ORDERS if py else []:
        done = subprocess.run(
            ['uv', 'run', 'ruff', *order, '--config', str(paths.ROOT / 'pyproject.toml'), *py],
            cwd=paths.ROOT,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
        )
        if done.returncode:
            problems.append((done.stdout + done.stderr).strip())
    return {'stage': 'lint', 'status': 'fail' if problems else 'pass', 'detail': '\n'.join(problems)}
