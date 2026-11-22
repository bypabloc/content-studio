"""Tabla `subtitle_projects` (spec 014, D-1): nombre y rutas del proyecto; el documento vive en su `subtitles.json`."""

from __future__ import annotations

import sqlite3

from content_studio.db.connection import utc_now


def insert(conn: sqlite3.Connection, name: str, source_path: str, doc_path: str) -> int:
    """Registra un proyecto y devuelve su id."""
    now = utc_now()
    cursor = conn.execute(
        'INSERT INTO subtitle_projects (name, source_path, doc_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
        (name, source_path, doc_path, now, now),
    )
    project_id = cursor.lastrowid
    assert project_id is not None  # un INSERT siempre deja el id de la fila
    return project_id


def get(conn: sqlite3.Connection, project_id: int) -> dict | None:
    """El proyecto, o None si no existe."""
    row = conn.execute('SELECT * FROM subtitle_projects WHERE id = ?', (project_id,)).fetchone()
    return None if row is None else dict(row)


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    """Los proyectos, del más reciente al más antiguo."""
    return [dict(row) for row in conn.execute('SELECT * FROM subtitle_projects ORDER BY id DESC')]


def touch(conn: sqlite3.Connection, project_id: int) -> None:
    """Marca el proyecto como editado ahora."""
    conn.execute('UPDATE subtitle_projects SET updated_at = ? WHERE id = ?', (utc_now(), project_id))


def delete(conn: sqlite3.Connection, project_id: int) -> None:
    """Quita el registro; la carpeta del documento la mueve la ruta que borra."""
    conn.execute('DELETE FROM subtitle_projects WHERE id = ?', (project_id,))
