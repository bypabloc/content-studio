"""Servicio `library.scan` (spec 020, D-1): recorre las carpetas vigiladas de la biblioteca.

Solo lee el disco y ffprobe: no toma el candado de la GPU. La base la recibe por `CONTENT_STUDIO_DB` (runner).
"""

from __future__ import annotations

import sys
from pathlib import Path

KIND = 'library.scan'
RESOURCE = 'cpu'


def validate(params: dict) -> list[dict]:
    """`folder_id` es opcional; si viene, es un entero positivo."""
    folder = params.get('folder_id')
    if folder is not None and (not isinstance(folder, int) or isinstance(folder, bool) or folder < 1):
        return [{'code': 'invalid_folder', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """`python -m content_studio.library.scan [--folder ID]`."""
    command = [sys.executable, '-m', 'content_studio.library.scan']
    if params.get('folder_id') is not None:
        command += ['--folder', str(params['folder_id'])]
    return command
