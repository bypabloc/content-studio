"""Servicio de convertir (spec 015, D-1 a D-3): valida el formato y el encuadre, y arma el comando del conversor.

Es ffmpeg: no carga modelos, así que la cola no toma el candado de la GPU.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from content_studio.media.convert import available_encoders
from content_studio.media.formats import TARGETS

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU
REFRAME_MODES = ('center', 'manual', 'fit-bars', 'fit-blur', 'follow-face')


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}: el formato debe existir, su códec estar en el ffmpeg del equipo y el encuadre
    ser un modo conocido. Así el error llega al encolar y no al final del trabajo."""
    target = params.get('target')
    if target not in TARGETS:
        return [{'code': 'unknown_target', 'params': {'target': target}}]
    codec = TARGETS[target]['codec']
    if codec not in available_encoders():
        return [{'code': 'codec_unavailable', 'params': {'codec': codec}}]
    reframe = (params.get('options') or {}).get('reframe') or {}
    mode = reframe.get('mode')
    if mode is not None and mode not in REFRAME_MODES:
        return [{'code': 'unknown_reframe', 'params': {'mode': mode}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.media.convert`: el resultado sale en la carpeta del trabajo, `converted.<ext>`."""
    return [
        sys.executable,
        '-m',
        'content_studio.media.convert',
        '--input',
        str(params['input']),
        '--target',
        params['target'],
        '--out-dir',
        str(output_dir),
        '--options',
        json.dumps(params.get('options') or {}),
    ]
