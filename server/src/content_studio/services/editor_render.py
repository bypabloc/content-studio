"""Servicio `editor.render` (spec 017, D-4): render de audio de un proyecto del editor, en la cola, sin candado de GPU.

El trabajo corre `content_studio.editor.render_main` y deja el archivo en `exports/` del proyecto.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from content_studio.media import formats, normalize

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def validate(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Errores como {'code', 'params'}: sin proyecto, un formato de audio que no existe o un preset que no existe."""
    errors: list[dict[str, Any]] = []
    if not params.get('doc'):
        errors.append({'code': 'editor_project_not_found', 'params': {'path': ''}})
    target = formats.TARGETS.get(params.get('format', 'wav'))
    if target is None or target['kind'] != 'audio':
        errors.append({'code': 'unknown_target', 'params': {'target': params.get('format')}})
    preset = params.get('normalize')
    if preset is not None and preset not in normalize.TARGETS:
        errors.append({'code': 'unknown_preset', 'params': {'preset': preset}})
    return errors


def build_command(params: dict[str, Any], output_dir: Path) -> list[str]:
    """Comando de `content_studio.editor.render_main`: el `project.json`, el formato, la sonoridad y la carpeta."""
    command = [
        sys.executable,
        '-m',
        'content_studio.editor.render_main',
        '--project',
        str(params['doc']),
        '--format',
        str(params.get('format', 'wav')),
    ]
    if params.get('normalize'):
        command += ['--normalize', str(params['normalize'])]
    return [*command, '--out-dir', str(output_dir)]
