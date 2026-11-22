"""Servicio `subtitles.burn` (spec 014, D-7): quema el documento de un proyecto en su video con ffmpeg y libass."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from content_studio.db import subtitle_projects
from content_studio.media import formats
from content_studio.subtitles import styles
from content_studio.system import tools

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU
ERROR_CODES = {3: 'ffmpeg_no_libass'}  # el código de salida de burn_main sin libass


def prepare(conn: sqlite3.Connection, params: dict) -> tuple[dict, None]:
    """Agrega la ruta del documento y del video del proyecto. Sin proyecto no agrega nada y `validate` lo rechaza."""
    project_id = params.get('project_id')
    project = subtitle_projects.get(conn, project_id) if isinstance(project_id, int) else None
    if project is None:
        return params, None
    return {**params, 'doc': project['doc_path'], 'source': project['source_path']}, None


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el proyecto se puede quemar."""
    if not params.get('doc'):
        return [{'code': 'subtitle_project_not_found', 'params': {'project_id': params.get('project_id')}}]
    errors = []
    preset = params.get('preset')
    if preset is not None and preset not in styles.PRESETS:
        errors.append({'code': 'unknown_style', 'params': {'style': preset}})
    if not formats.is_video(Path(params['source'])):
        errors.append({'code': 'burn_needs_video', 'params': {}})
    if not tools.detect()['subtitles_filter']:
        errors.append({'code': 'ffmpeg_no_libass', 'params': {}})
    return errors


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.subtitles.burn_main`: el documento, el preset si lo hay y la carpeta del trabajo."""
    command = [sys.executable, '-m', 'content_studio.subtitles.burn_main', '--doc', str(params['doc'])]
    command += ['--out', str(output_dir)]
    if params.get('preset'):
        command += ['--preset', params['preset']]
    return command
