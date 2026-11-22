"""Explorador de solo lectura del editor (spec 017, D-10, AC-3): raíces, carpetas y medios. No escribe nada.

Los nombres que empiezan por punto no salen. Los archivos ocultos de Windows (atributo) quedan pendientes.
"""

from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from content_studio.api.errors import ApiError
from content_studio.media import formats

router = APIRouter(prefix='/fs')
KIND_EXTENSIONS = {'audio': formats.AUDIO_EXTENSIONS, 'video': formats.VIDEO_EXTENSIONS}
KNOWN_FOLDERS = (
    ('desktop', 'Desktop'),  # i18n-ignore: nombre de carpeta del perfil en disco
    ('music', 'Music'),  # i18n-ignore: nombre de carpeta del perfil en disco
    ('videos', 'Videos'),  # i18n-ignore: nombre de carpeta del perfil en disco
    ('downloads', 'Downloads'),  # i18n-ignore: nombre de carpeta del perfil en disco
)


@router.get('/roots')
def roots() -> dict[str, list[dict[str, str]]]:
    """Las raíces del explorador: la carpeta de usuario, sus carpetas conocidas y las unidades que existen."""
    home = Path.home()
    found = [{'name': 'home', 'path': str(home)}]
    found += [{'name': name, 'path': str(home / folder)} for name, folder in KNOWN_FOLDERS if (home / folder).is_dir()]
    if os.name == 'nt':
        drives = (f'{letter}:\\' for letter in string.ascii_uppercase)
        found += [{'name': drive[:2], 'path': drive} for drive in drives if Path(drive).exists()]
    return {'roots': found}


@router.get('/list')
def list_folder(path: str, kinds: str = 'audio,video') -> dict[str, Any]:
    """Las carpetas de `path` y los medios de los tipos pedidos (`audio`, `video`), carpetas primero."""
    folder = Path(path)
    if not folder.is_dir():
        raise ApiError(404, 'fs_path_not_found', path=path)
    wanted = {ext: kind for kind in kinds.split(',') if kind in KIND_EXTENSIONS for ext in KIND_EXTENSIONS[kind]}
    try:
        children = sorted(folder.iterdir(), key=lambda child: (not child.is_dir(), child.name.lower()))
    except PermissionError as error:
        raise ApiError(403, 'fs_forbidden', path=path) from error
    entries: list[dict[str, Any]] = []
    for child in children:
        if child.name.startswith('.'):
            continue
        if child.is_dir():
            entries.append({'name': child.name, 'path': str(child), 'kind': 'folder'})
        elif child.suffix.lower() in wanted:
            stat = child.stat()
            entries.append(
                {
                    'name': child.name,
                    'path': str(child),
                    'kind': wanted[child.suffix.lower()],
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                }
            )
    return {'path': str(folder), 'entries': entries}
