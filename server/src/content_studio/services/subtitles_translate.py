"""Servicio `subtitles.translate` (spec 014, D-8): traduce al inglés con faster-whisper sobre el video del proyecto."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from content_studio.db import subtitle_projects
from content_studio.transcription import models

RESOURCE = 'gpu'  # whisper carga un modelo: toma el candado de la GPU


def prepare(conn: sqlite3.Connection, params: dict) -> tuple[dict, None]:
    """Agrega el documento y el video del proyecto. Sin proyecto no agrega nada y `validate` lo rechaza."""
    project = subtitle_projects.get(conn, params.get('project_id'))
    if project is None:
        return params, None
    return {**params, 'doc': project['doc_path'], 'source': project['source_path']}, None


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el proyecto se puede traducir."""
    if not params.get('doc'):
        return [{'code': 'subtitle_project_not_found', 'params': {'project_id': params.get('project_id')}}]
    model = params.get('model', models.recommended())
    if model not in models.MODELS:
        return [{'code': 'unknown_engine', 'params': {'model': model}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """`transcribe_main` con `--task translate`: escribe `words.json` (segmentos en inglés) en la carpeta."""
    return [
        sys.executable,
        '-m',
        'content_studio.transcription.transcribe_main',
        '--input',
        str(params['source']),
        '--model',
        params.get('model', models.recommended()),
        '--language',
        params.get('language', 'auto'),
        '--task',
        'translate',
        '--out',
        str(output_dir / 'words.json'),
    ]
