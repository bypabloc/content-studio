"""Servicio `editor.render` (spec 017, D-4): render de audio de un proyecto del editor, en la cola, sin candado de GPU.

El trabajo corre `content_studio.editor.render_main` y deja el archivo en `exports/` del proyecto.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

from content_studio.media import formats, normalize

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU
ERROR_CODES = {3: 'missing_source'}


def validate(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Errores como {'code', 'params'}: sin proyecto, un formato que no existe o un preset inválido."""
    errors: list[dict[str, Any]] = []
    if not params.get('doc'):
        errors.append({'code': 'editor_project_not_found', 'params': {'path': ''}})
    target = formats.TARGETS.get(params.get('format', 'wav'))
    if target is None or target['kind'] not in {'audio', 'video'}:
        errors.append({'code': 'unknown_target', 'params': {'target': params.get('format')}})
    quality = params.get('quality')
    if 'quality' in params and (
        target is None
        or target['kind'] != 'video'
        or not isinstance(quality, int)
        or isinstance(quality, bool)
        or not 0 <= quality <= 51
    ):
        errors.append({'code': 'invalid_video_quality', 'params': {'quality': quality}})
    preset = params.get('normalize')
    if preset is not None and preset not in normalize.TARGETS:
        errors.append({'code': 'unknown_preset', 'params': {'preset': preset}})
    if 'start' in params or 'end' in params:
        start, end = params.get('start'), params.get('end')
        if (
            not isinstance(start, (int, float))
            or isinstance(start, bool)
            or not isinstance(end, (int, float))
            or isinstance(end, bool)
            or not math.isfinite(start)
            or not math.isfinite(end)
            or start < 0
            or end <= start
        ):
            errors.append({'code': 'bad_render_range', 'params': {'start': start, 'end': end}})
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
    if 'quality' in params:
        command += ['--quality', str(params['quality'])]
    if 'start' in params:
        command += ['--start', str(params['start'])]
    if 'end' in params:
        command += ['--end', str(params['end'])]
    if params.get('name'):
        command += ['--name', str(params['name'])]
    return [*command, '--out-dir', str(output_dir)]
