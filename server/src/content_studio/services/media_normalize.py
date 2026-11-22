"""Servicio de normalizar (spec 015, D-4): valida el preset y la ruta, y arma el comando de `media.normalize`.

Es ffmpeg: no carga modelos, así que la cola no toma el candado de la GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.media import normalize

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el trabajo puede correr."""
    errors = []
    preset = params.get('preset')
    if preset not in normalize.PRESETS:
        errors.append({'code': 'unknown_preset', 'params': {'preset': preset}})
    reference = normalize.reference_error(params.get('input', ''))
    if reference is not None:
        errors.append(reference)
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.media.normalize`: el archivo y su reporte salen en la carpeta del trabajo."""
    source = Path(params['input'])
    command = [
        sys.executable,
        '-m',
        'content_studio.media.normalize',
        '--input',
        str(source),
        '--out',
        str(output_dir / f'normalized{source.suffix}'),
        '--preset',
        params['preset'],
        '--report',
        str(output_dir / 'result.json'),
    ]
    if params['preset'] == 'custom':
        command += ['--target', str(params['target'])]
    if params.get('enhance'):
        command.append('--enhance')
    return command
