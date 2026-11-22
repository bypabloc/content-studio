"""Tabla `mix_projects` (spec 016, D-3): nombre y ruta del proyecto; el documento vive en su `mix.json`."""

from __future__ import annotations

import sqlite3

from content_studio.db.connection import utc_now


def insert(conn: sqlite3.Connection, name: str, doc_path: str) -> int:
    """Registra el proyecto y devuelve su id. La ruta del documento se fija después, con su id en la carpeta."""
    now = utc_now()
    cursor = conn.execute(
        'INSERT INTO mix_projects (name, doc_path, created_at, updated_at) VALUES (?, ?, ?, ?)',
        (name, doc_path, now, now),
    )
    project_id = cursor.lastrowid
    assert project_id is not None  # un INSERT siempre deja el id de la fila
    return project_id


def get(conn: sqlite3.Connection, project_id: int) -> dict | None:
    """El proyecto, o None si no existe."""
    row = conn.execute('SELECT * FROM mix_projects WHERE id = ?', (project_id,)).fetchone()
    return None if row is None else dict(row)


def set_doc_path(conn: sqlite3.Connection, project_id: int, doc_path: str) -> None:
    """Fija la ruta del `mix.json` una vez que la carpeta del proyecto existe."""
    conn.execute('UPDATE mix_projects SET doc_path = ? WHERE id = ?', (doc_path, project_id))


def touch(conn: sqlite3.Connection, project_id: int) -> None:
    """Marca el proyecto como cambiado ahora."""
    conn.execute('UPDATE mix_projects SET updated_at = ? WHERE id = ?', (utc_now(), project_id))
