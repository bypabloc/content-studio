"""Caché de transcripciones (spec 013, D-4): la tabla `transcripts` guarda rutas y metadatos; el JSON va en disco."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from content_studio import paths
from content_studio.db.connection import utc_now


def cache_key(source_path: str, source_mtime: float, model: str, language: str) -> str:
    """sha1 de ruta, mtime, modelo e idioma: nombre del JSON de la transcripción."""
    text = f'{source_path}|{source_mtime}|{model}|{language}'
    return hashlib.sha1(text.encode('utf-8'), usedforsecurity=False).hexdigest()


def json_path(key: str) -> Path:
    """Dónde va el JSON de una transcripción: `<datos>/transcripts/<clave>.json`."""
    return paths.data_dir() / 'transcripts' / f'{key}.json'


def find(
    conn: sqlite3.Connection, source_path: str, source_mtime: float, source_size: int, model: str, language: str
) -> str | None:
    """Ruta del JSON si ya hay una transcripción de ese archivo, modelo e idioma; None si no (o si el JSON falta)."""
    row = conn.execute(
        'SELECT json_path FROM transcripts '
        'WHERE source_path = ? AND source_mtime = ? AND source_size = ? AND model = ? AND language = ? '
        'ORDER BY id DESC LIMIT 1',
        (source_path, source_mtime, source_size, model, language),
    ).fetchone()
    if row is None or not Path(row['json_path']).exists():
        return None
    return row['json_path']


def store(
    conn: sqlite3.Connection,
    source_path: str,
    source_mtime: float,
    source_size: int,
    model: str,
    language: str,
    json_file: str,
) -> None:
    """Registra la transcripción: la ruta de su JSON y los metadatos del archivo, nunca el texto."""
    conn.execute(
        'INSERT INTO transcripts (source_path, source_mtime, source_size, model, language, json_path, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (source_path, source_mtime, source_size, model, language, json_file, utc_now()),
    )
