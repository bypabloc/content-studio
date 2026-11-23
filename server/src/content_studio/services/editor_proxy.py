"""Servicio `editor.proxy` (spec 018, D-3): crea un proxy de video en la caché del proyecto."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from content_studio.editor import store
from content_studio.media.formats import is_video

RESOURCE = 'cpu'
ERROR_CODES = {3: 'unreadable_media'}


def validate(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Valida el proyecto del editor y la fuente de video antes de encolar."""
    project = Path(str(params.get('project', '')))
    source = Path(str(params.get('source', '')))
    if project.name != store.FILE or not project.is_file():
        return [{'code': 'editor_project_not_found', 'params': {'path': str(project)}}]
    if not source.is_absolute():
        source = project.resolve().parent / source
    if not source.is_file():
        return [{'code': 'fs_media_not_found', 'params': {'path': str(source)}}]
    if not is_video(source):
        return [{'code': 'unreadable_media', 'params': {}}]
    return []


def build_command(params: dict[str, Any], output_dir: Path) -> list[str]:
    """Ejecuta `content_studio.editor.proxy`; el archivo resultante va en la caché del proyecto."""
    return [
        sys.executable,
        '-m',
        'content_studio.editor.proxy',
        '--project',
        str(params['project']),
        '--source',
        str(params['source']),
    ]
