"""Servicio `diarize.split` (spec 035, AC-5): un WAV por hablante, en la CPU; arma el comando de job_main split."""

from __future__ import annotations

import sys
from pathlib import Path

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}: el audio debe existir, y la carpeta de turnos debe tener turns.json."""
    errors = []
    source = params.get('input')
    if not source or not Path(source).is_file():
        errors.append({'code': 'file_not_found', 'params': {'path': str(source or '')}})
    turns = params.get('turns')
    if not turns or not (Path(turns) / 'turns.json').is_file():
        errors.append({'code': 'not_a_diarization', 'params': {}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.diarization.job_main split`: el audio, sus turnos y la carpeta del trabajo."""
    return [
        sys.executable,
        '-m',
        'content_studio.diarization.job_main',
        'split',
        '--input',
        str(params['input']),
        '--turns',
        str(params['turns']),
        '--out',
        str(output_dir),
    ]
