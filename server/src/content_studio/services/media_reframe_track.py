"""Servicio de seguimiento de la persona (spec 015, D-3): corre `face_track_main` en `.venv-vision` y deja `track.json`.

Sin modelos de la GPU: YuNet corre en CPU, así que la cola no toma el candado.
"""

from __future__ import annotations

import sys
from pathlib import Path

RESOURCE = 'cpu'  # YuNet corre en CPU: no carga modelos de la GPU, así que no toma el candado


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el trabajo puede correr."""
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.vision.face_track_main`; el `track.json` sale en la carpeta del trabajo."""
    return [
        sys.executable,
        '-m',
        'content_studio.vision.face_track_main',
        '--input',
        str(params['input']),
        '--out',
        str(output_dir / 'track.json'),
    ]
