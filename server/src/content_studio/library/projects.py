"""Proyectos de la biblioteca (spec 020, D-3): agrupan ítems sin copiar archivos; borrar uno solo borra el grupo."""

from __future__ import annotations

import sqlite3

from content_studio.db.connection import utc_now


def _name(value: str) -> str:
    name = ' '.join(value.split())
    if not name:
        raise ValueError('empty project name')
    return name


def get(conn: sqlite3.Connection, project_id: int) -> dict:
    """El proyecto con su cantidad de ítems. LookupError si no existe."""
    row = conn.execute(
        'SELECT p.*, COUNT(pi.item_id) AS count FROM projects p LEFT JOIN project_items pi ON pi.project_id = p.id '
        'WHERE p.id = ? GROUP BY p.id',
        (project_id,),
    ).fetchone()
    if row is None:
        raise LookupError(f'project {project_id} does not exist')
    return dict(row)


def create(conn: sqlite3.Connection, value: str) -> dict:
    """Crea un proyecto vacío."""
    project_id = conn.execute(
        'INSERT INTO projects (name, created_at) VALUES (?, ?)', (_name(value), utc_now())
    ).lastrowid
    assert project_id is not None  # un INSERT siempre deja el id
    return get(conn, project_id)


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    """Los proyectos, del más nuevo al más antiguo, con su cantidad de ítems."""
    rows = conn.execute(
        'SELECT p.*, COUNT(pi.item_id) AS count FROM projects p LEFT JOIN project_items pi ON pi.project_id = p.id '
        'GROUP BY p.id ORDER BY p.id DESC'
    )
    return [dict(row) for row in rows]


def rename(conn: sqlite3.Connection, project_id: int, value: str) -> dict:
    """Cambia el nombre. LookupError si no existe."""
    name = _name(value)
    get(conn, project_id)
    conn.execute('UPDATE projects SET name = ? WHERE id = ?', (name, project_id))
    return get(conn, project_id)


def delete(conn: sqlite3.Connection, project_id: int) -> bool:
    """Borra el proyecto (y sus relaciones); los ítems y archivos quedan. False si no existía."""
    return conn.execute('DELETE FROM projects WHERE id = ?', (project_id,)).rowcount > 0


def add_items(conn: sqlite3.Connection, project_id: int, items: list[int]) -> None:
    """Agrega ítems al proyecto (los repetidos, una vez). LookupError si no existe el proyecto o un ítem."""
    get(conn, project_id)
    for item_id in items:
        if conn.execute('SELECT 1 FROM library_items WHERE id = ?', (item_id,)).fetchone() is None:
            raise LookupError(item_id)
        conn.execute('INSERT OR IGNORE INTO project_items (project_id, item_id) VALUES (?, ?)', (project_id, item_id))


def remove_item(conn: sqlite3.Connection, project_id: int, item_id: int) -> bool:
    """Quita el ítem del proyecto. False si no estaba."""
    return (
        conn.execute('DELETE FROM project_items WHERE project_id = ? AND item_id = ?', (project_id, item_id)).rowcount
        > 0
    )
