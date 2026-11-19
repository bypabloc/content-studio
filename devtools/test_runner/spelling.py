"""Etapa `spelling`: cspell sobre los archivos del changeset (spec 003, D-1).

La lógica vive en devtools/spelling.py (`review`); esta etapa solo la adapta al formato `{stage, status, detail}`.
"""

from __future__ import annotations

from pathlib import Path

from .. import paths, spelling


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Pasa sin archivos (no corre cspell). Falla con cada palabra desconocida, o con el error de cspell."""
    if not files:
        return {'stage': 'spelling', 'status': 'pass', 'detail': ''}
    try:
        issues = spelling.review(files)
    except RuntimeError as error:
        return {'stage': 'spelling', 'status': 'fail', 'detail': str(error)}
    return {'stage': 'spelling', 'status': 'fail' if issues else 'pass', 'detail': '\n'.join(issues)}
