"""Servicio `mix.render` (spec 016, D-2): mezcla un proyecto con ffmpeg; no toma el candado de la GPU."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from content_studio.db import mix_projects

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def prepare(conn: sqlite3.Connection, params: dict) -> tuple[dict, None]:
    """Agrega la ruta del `mix.json` del proyecto. Sin proyecto no agrega nada y `validate` lo rechaza."""
    project_id = params.get('mix_id')
    row = mix_projects.get(conn, project_id) if isinstance(project_id, int) else None
    if row is None:
        return params, None
    return {**params, 'doc': row['doc_path']}, None


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el proyecto existe."""
    if not params.get('doc'):
        return [{'code': 'mix_project_not_found', 'params': {'project_id': params.get('mix_id')}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.mix.render_main`: el `mix.json` del proyecto y la carpeta del trabajo."""
    return [
        sys.executable,
        '-m',
        'content_studio.mix.render_main',
        '--project',
        str(params['doc']),
        '--out-dir',
        str(output_dir),
    ]
