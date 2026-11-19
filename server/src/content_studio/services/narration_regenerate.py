"""Servicio narration.regenerate (spec 006, D-2): rehace un bloque de una toma y escribe una toma nueva."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from content_studio import paths
from content_studio.db import jobs
from content_studio.narration.engines.registry import ENGINES

RESOURCE = 'gpu'  # la cola lo corre con el candado de la GPU: un modelo a la vez
SOURCES = ('narration', 'narration.regenerate')  # trabajos de los que se puede rehacer un bloque


def prepare(conn: sqlite3.Connection, params: dict) -> tuple[dict, str | None]:
    """Resuelve `source_job` (un trabajo de narración ya terminado): su carpeta, su motor y su grupo de tomas.
    Si no sirve, devuelve los parámetros sin resolver y `validate` lo rechaza."""
    source = jobs.get(conn, params['source_job']) if isinstance(params.get('source_job'), int) else None
    if source is None or source['status'] != 'done' or source['kind'] not in SOURCES:
        return params, None
    resolved = {**params, 'source': source['output_dir'], 'model': source['params']['model']}
    return resolved, source['group_key']


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si la toma existe, el bloque cae dentro y el motor está instalado."""
    source = params.get('source')
    if source is None:  # sin toma no hay motor que comprobar: el error es solo ese
        return [{'code': 'source_not_done', 'params': {'job': params.get('source_job')}}]
    errors = []
    model = params.get('model')
    if model not in ENGINES:
        errors.append({'code': 'unknown_engine', 'params': {'model': model}})
    elif not ENGINES[model].installed():
        errors.append({'code': 'engine_not_installed', 'params': {'model': model}})
    folder = Path(source).resolve()
    if not folder.is_relative_to(paths.OUT.resolve()):  # solo se leen tomas que el propio studio escribió
        return [*errors, {'code': 'source_outside_out', 'params': {'source': source}}]
    if not (folder / 'script.json').is_file():
        return [*errors, {'code': 'source_missing', 'params': {'source': source}}]
    blocks = len(json.loads((folder / 'script.json').read_text(encoding='utf-8'))['segments'])
    index = params.get('index')
    if not isinstance(index, int) or not 0 <= index < blocks:
        errors.append({'code': 'index_out_of_range', 'params': {'index': index, 'blocks': blocks}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.narration.tts` con `--from-script`: rehace solo el bloque `--only` de la toma."""
    args = [
        '--model', params['model'], '--from-script', params['source'], '--only', str(params['index']),
        '--output', str(output_dir),
    ]  # fmt: skip
    if 'seed' in params:
        args += ['--seed', str(params['seed'])]
    return [sys.executable, '-m', 'content_studio.narration.tts', *args]
