"""Servicio `clean.analyze` (spec 013, D-4): valida el pedido y arma el comando de `analyze_main`."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.services.transcribe import LANGUAGES
from content_studio.transcription import models

RESOURCE = 'gpu'  # transcribe carga el modelo: la cola lo corre con el candado de la GPU


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el análisis puede correr."""
    errors = []
    if not params.get('input'):
        errors.append({'code': 'missing_input', 'params': {}})
    model = params.get('model')
    if model not in models.MODELS:
        errors.append({'code': 'unknown_engine', 'params': {'model': model}})
    language = params.get('language', 'auto')
    if language not in LANGUAGES:
        errors.append({'code': 'unknown_language', 'params': {'language': language}})
    if params.get('min_gap', 0.5) < 0 or params.get('padding', 0.15) < 0:
        errors.append({'code': 'invalid_gap', 'params': {}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.clean.analyze_main`; `cuts.json` queda en la carpeta del trabajo."""
    args = [
        '--input', str(params['input']),
        '--model', params['model'],
        '--language', params.get('language', 'auto'),
        '--min-gap', str(params.get('min_gap', 0.5)),
        '--padding', str(params.get('padding', 0.15)),
        '--folder', str(output_dir),
    ]  # fmt: skip
    args.append('--edges' if params.get('edges', True) else '--no-edges')
    return [sys.executable, '-m', 'content_studio.clean.analyze_main', *args]
