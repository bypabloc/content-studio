"""Servicio de música (spec 004, D-2): valida los parámetros de la cola y arma el comando de `music_main`."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.music.parser import MODELS, STYLES

RESOURCE = 'gpu'  # la cola lo corre con el candado de la GPU: un modelo a la vez
DEFAULT_DURATION = 60  # el mismo default que el parser
# shortcut: copia de los límites del help del parser (ACE ≤600, HeartMuLa ≤240), subir a MusicSpec si cambian
MAX_SECONDS = {'acestep': 600, 'heartmula': 240}
# Flags que pasan tal cual del trabajo al CLI del motor.
FLAGS = {
    'key': '--key',
    'bpm': '--bpm',
    'time_signature': '--time-signature',
    'variants': '--variants',
    'retries': '--retries',
}


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el trabajo puede correr."""
    errors = []
    model = params.get('model')
    if model not in MODELS:
        errors.append({'code': 'unknown_engine', 'params': {'model': model}})
    elif not MODELS[model].installed():
        errors.append({'code': 'engine_not_installed', 'params': {'model': model}})
    if not params.get('style'):
        errors.append({'code': 'missing_style', 'params': {}})
    for style in params.get('style', []):
        if style not in STYLES and not (params.get('key') and params.get('bpm')):
            errors.append({'code': 'style_needs_key_bpm', 'params': {'style': style}})
    duration = params.get('duration', DEFAULT_DURATION)
    if model in MAX_SECONDS and not 0 < duration <= MAX_SECONDS[model]:
        errors.append({'code': 'invalid_duration', 'params': {'max': MAX_SECONDS[model]}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.music.music_main`; `--folder` es la carpeta del trabajo."""
    args = [
        '--model',
        params['model'],
        '--style',
        *params['style'],
        '--duration',
        str(params.get('duration', DEFAULT_DURATION)),
        '--folder',
        str(output_dir),
    ]
    for key, flag in FLAGS.items():
        if key in params:
            args += [flag, str(params[key])]
    if params.get('evaluate'):
        args.append('--evaluate')
    return [sys.executable, '-m', 'content_studio.music.music_main', *args]
