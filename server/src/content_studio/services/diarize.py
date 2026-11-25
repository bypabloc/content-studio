"""Servicio `diarize` (spec 035, AC-7): valida el audio, los hablantes y el motor, y arma el comando de job_main."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.diarization import diarize_main

RESOURCE = 'gpu'  # pyannote carga el modelo: la cola la corre con el candado de la GPU
MAX_SPEAKERS = 20


def speaker_errors(params: dict) -> list[dict]:
    """Errores de los hablantes pedidos: cada número de 1 a 20, y el mínimo no mayor que el máximo."""
    counts = [params.get(key) for key in diarize_main.SPEAKER_FLAGS]
    if any(value is not None and not 1 <= value <= MAX_SPEAKERS for value in counts):
        return [{'code': 'invalid_speakers', 'params': {}}]
    low, high = params.get('min_speakers'), params.get('max_speakers')
    if low is not None and high is not None and low > high:
        return [{'code': 'invalid_speakers', 'params': {}}]
    return []


def speaker_flags(params: dict) -> list[str]:
    """Los flags de hablantes que el trabajo pidió: --speakers, --min-speakers o --max-speakers."""
    flags: list[str] = []
    for key, flag in diarize_main.SPEAKER_FLAGS.items():
        if params.get(key) is not None:
            flags += [flag, str(params[key])]
    return flags


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el trabajo puede correr."""
    errors = []
    source = params.get('input')
    if not source or not Path(source).is_file():
        errors.append({'code': 'file_not_found', 'params': {'path': str(source or '')}})
    errors += speaker_errors(params)
    if not diarize_main.available():
        errors.append({'code': 'engine_not_installed', 'params': {'model': 'pyannote'}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.diarization.job_main diarize`: el audio, la carpeta del trabajo y los hablantes."""
    return [
        sys.executable,
        '-m',
        'content_studio.diarization.job_main',
        'diarize',
        '--input',
        str(params['input']),
        '--out',
        str(output_dir),
        *speaker_flags(params),
    ]
