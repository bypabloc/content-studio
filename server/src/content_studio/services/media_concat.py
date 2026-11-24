"""Servicio de unir (spec 015, D-5): valida que los archivos sean del mismo tipo y arma el comando de `edit concat`.

Es ffmpeg: no carga modelos, así que la cola no toma el candado de la GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.media import edit

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}: al menos dos archivos, y todos audio o todos video (`mixed_kinds`)."""
    inputs = params.get('inputs', [])
    if len(inputs) < 2:
        return [{'code': 'missing_input', 'params': {}}]
    if len({edit.has_video(path) for path in inputs}) > 1:
        return [{'code': 'mixed_kinds', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.media.edit concat`: la unión sale en MP4 si es video y en WAV si es audio."""
    inputs = [str(path) for path in params['inputs']]
    out = output_dir / ('joined.mp4' if edit.has_video(inputs[0]) else 'joined.wav')
    return [
        sys.executable,
        '-m',
        'content_studio.media.edit',
        'concat',
        '--input',
        *inputs,
        '--out',
        str(out),
        '--crossfade',
        str(params.get('crossfade', 0.0)),
    ]
