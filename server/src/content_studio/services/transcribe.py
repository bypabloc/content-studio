"""Servicio de transcripción (spec 013, D-2 y D-4): valida los parámetros y arma el comando de `transcribe_main`."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.transcription import models

RESOURCE = 'gpu'  # la transcripción carga el modelo: la cola la corre con el candado de la GPU
LANGUAGES = ('auto', 'es', 'en', 'pt', 'fr', 'de', 'it')  # «auto» deja que el modelo detecte el idioma


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el trabajo puede correr."""
    errors = []
    model = params.get('model')
    if model not in models.MODELS:
        errors.append({'code': 'unknown_engine', 'params': {'model': model}})
    language = params.get('language', 'auto')
    if language not in LANGUAGES:
        errors.append({'code': 'unknown_language', 'params': {'language': language}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.transcription.transcribe_main`; el JSON sale en la carpeta del trabajo."""
    return [
        sys.executable,
        '-m',
        'content_studio.transcription.transcribe_main',
        '--input',
        str(params['input']),
        '--model',
        params['model'],
        '--language',
        params.get('language', 'auto'),
        '--out',
        str(output_dir / 'words.json'),
    ]
