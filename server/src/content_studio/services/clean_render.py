"""Servicio `clean.render` (spec 013, D-4): valida el render y arma el comando de `render_main`."""

from __future__ import annotations

import sys
from pathlib import Path

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el render puede correr."""
    errors = []
    if not params.get('input'):
        errors.append({'code': 'missing_input', 'params': {}})
    if not params.get('analysis'):
        errors.append({'code': 'missing_analysis', 'params': {}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.clean.render_main`: el original, la carpeta del análisis y la salida del trabajo."""
    return [
        sys.executable,
        '-m',
        'content_studio.clean.render_main',
        '--input',
        str(params['input']),
        '--analysis',
        str(params['analysis']),
        '--out',
        str(output_dir),
    ]
