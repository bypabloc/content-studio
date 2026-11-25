"""Servicio `subtitles.create` (spec 014, D-4): valida el origen y arma el comando de `create_main`.

RESOURCE es 'gpu' porque los orígenes de archivo y de narración transcriben. El del limpiador y el importado no
necesitan GPU, pero el servicio es uno solo; la decisión está en WARNING 014-origenes-gpu.
"""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.diarization import diarize_main
from content_studio.services import diarize as diarize_service
from content_studio.transcription import models

RESOURCE = 'gpu'
ORIGINS = ('file', 'cleaner', 'narration', 'import')
_TRANSCRIBES = ('file', 'narration')
_IMPORT_SUFFIXES = ('.srt', '.vtt')


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el documento puede crearse."""
    origin = params.get('origin')
    if origin not in ORIGINS:
        return [{'code': 'unknown_origin', 'params': {'origin': origin}}]
    errors = []
    if not params.get('input'):
        code = 'missing_transcript' if origin == 'cleaner' else 'missing_input'
        errors.append({'code': code, 'params': {}})
    if origin == 'cleaner' and not params.get('analysis'):
        errors.append({'code': 'missing_analysis', 'params': {}})
    if origin == 'narration' and not params.get('script'):
        errors.append({'code': 'missing_script', 'params': {}})
    if origin == 'import' and params.get('input') and Path(params['input']).suffix.lower() not in _IMPORT_SUFFIXES:
        errors.append({'code': 'unsupported_subtitle_format', 'params': {'input': params['input']}})
    model = params.get('model', models.recommended())
    if origin in _TRANSCRIBES and model not in models.MODELS:
        errors.append({'code': 'unknown_engine', 'params': {'model': model}})
    if origin == 'file' and params.get('diarize'):
        errors += diarize_service.speaker_errors(params)
        if not diarize_main.available():
            errors.append({'code': 'engine_not_installed', 'params': {'model': 'pyannote'}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.subtitles.create_main`; `subtitles.json` queda en la carpeta del trabajo."""
    return [sys.executable, '-m', 'content_studio.subtitles.create_main', '--folder', str(output_dir)]
