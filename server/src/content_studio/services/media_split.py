"""Servicio de dividir (spec 015, D-5): valida el corte y arma el comando de `content_studio.media.edit split`.

Es ffmpeg: no carga modelos, así que la cola no toma el candado de la GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}: cada N segundos (> 0) o marcas crecientes y positivas."""
    markers, every = params.get('markers'), params.get('every')
    if markers:
        if markers[0] <= 0 or any(a >= b for a, b in zip(markers, markers[1:], strict=False)):
            return [{'code': 'invalid_split', 'params': {}}]
        return []
    if not every or every <= 0:
        return [{'code': 'invalid_split', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.media.edit split`: las partes salen en la carpeta del trabajo, `<nombre>-01.<ext>`."""
    source = Path(params['input'])
    cut = ['--markers', *map(str, params['markers'])] if params.get('markers') else ['--every', str(params['every'])]
    command = [
        sys.executable,
        '-m',
        'content_studio.media.edit',
        'split',
        '--input',
        str(source),
        '--out-dir',
        str(output_dir),
        '--stem',
        source.stem,
        *cut,
    ]
    if params.get('copy'):
        command.append('--copy')
    return command
