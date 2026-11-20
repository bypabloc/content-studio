"""Servicio de narración (spec 004, D-2): valida los parámetros de la cola y arma el comando de `narration.tts`."""

from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path

from content_studio.narration.parser import ENGINES, STYLES, approved_voices

RESOURCE = 'gpu'  # la cola lo corre con el candado de la GPU: un modelo a la vez
# Flags que pasan tal cual del trabajo al CLI del motor.
FLAGS = {
    'voice': '--voice',
    'language': '--language',
    'seed': '--seed',
    'master': '--master',
    'lufs': '--lufs',
    'batch': '--batch',
    'retries': '--retries',
    'ref': '--ref',
}


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el trabajo puede correr."""
    # shortcut: valida modelo, estilo, voz y guion; el parser valida el resto al arrancar el motor, y el trabajo queda
    # en error. Subir si la API necesita 422 para más campos.
    errors = []
    model = params.get('model')
    if model not in ENGINES:
        errors.append({'code': 'unknown_engine', 'params': {'model': model}})
    elif not ENGINES[model].installed():
        errors.append({'code': 'engine_not_installed', 'params': {'model': model}})
    if params.get('style') not in STYLES:
        errors.append({'code': 'unknown_style', 'params': {'style': params.get('style')}})
    if 'voice' in params and params['voice'] not in approved_voices(STYLES):
        errors.append({'code': 'unknown_voice', 'params': {'voice': params['voice']}})
    if not params.get('text') and not params.get('file'):
        errors.append({'code': 'missing_text', 'params': {}})
    if len(params.get('file') or []) > 1:  # una carpeta por toma (AC-2): un guion por trabajo
        errors.append({'code': 'one_script_per_job', 'params': {}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.narration.tts`; `--output` es la carpeta del trabajo (plan() la acepta)."""
    args = ['--model', params['model'], '--style', params['style'], '--output', str(output_dir)]
    for key, flag in FLAGS.items():
        if key in params:
            args += [flag, str(params[key])]
    if params.get('evaluate'):
        args.append('--evaluate')
    args += ['--text', params['text']] if 'text' in params else ['--file', *params['file']]
    return [sys.executable, '-m', 'content_studio.narration.tts', *args]


def group_key(params: dict) -> str | None:
    """Clave de las tomas de un mismo texto (spec 006, D-4): sha1 del texto con los espacios normalizados. Un archivo
    cuenta por su contenido; un trabajo sobre varios archivos no pertenece a ningún grupo."""
    if isinstance(params.get('text'), str):
        text = params['text']
    elif len(params.get('file') or []) == 1 and Path(params['file'][0]).is_file():
        text = Path(params['file'][0]).read_text(encoding='utf-8', errors='replace')
    else:
        return None
    digest = hashlib.sha1(' '.join(text.split()).encode('utf-8'), usedforsecurity=False).hexdigest()
    return f'narration:{digest[:12]}'


def prepare(conn: sqlite3.Connection, params: dict) -> tuple[dict, str | None]:
    """Antes de encolar: los parámetros tal cual y la clave de grupo del texto (la cola la guarda en el trabajo)."""
    return params, group_key(params)
