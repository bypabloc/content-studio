"""Tabla `subtitle_projects` (spec 014, D-1): la base guarda el nombre y las rutas; el documento vive en disco."""

from __future__ import annotations

from contextlib import closing

from content_studio.db import connection, schema, subtitle_projects


def _db(tmp_path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    return conn


def test_insert_and_get_keep_the_name_and_the_paths(tmp_path):
    """Lo que se inserta se lee igual; al crearse, `created_at` y `updated_at` coinciden."""
    with closing(_db(tmp_path)) as conn:
        project_id = subtitle_projects.insert(conn, 'charla', 'charla.mp4', 'out/charla/subtitles.json')

        project = subtitle_projects.get(conn, project_id)

    assert (project['name'], project['source_path'], project['doc_path']) == (
        'charla',
        'charla.mp4',
        'out/charla/subtitles.json',
    )
    assert project['created_at'] == project['updated_at']


def test_list_returns_the_most_recent_project_first(tmp_path):
    """La lista va del último registrado al primero."""
    with closing(_db(tmp_path)) as conn:
        first = subtitle_projects.insert(conn, 'uno', 'uno.mp4', 'out/uno/subtitles.json')
        second = subtitle_projects.insert(conn, 'dos', 'dos.mp4', 'out/dos/subtitles.json')

        ids = [project['id'] for project in subtitle_projects.list_projects(conn)]

    assert ids == [second, first]


def test_touch_moves_updated_at(tmp_path):
    """`touch` deja `updated_at` en el momento de la llamada (lo usa el PUT)."""
    with closing(_db(tmp_path)) as conn:
        project_id = subtitle_projects.insert(conn, 'charla', 'charla.mp4', 'out/subtitles.json')
        conn.execute("UPDATE subtitle_projects SET updated_at = '2000-01-01T00:00:00Z' WHERE id = ?", (project_id,))

        subtitle_projects.touch(conn, project_id)

        assert subtitle_projects.get(conn, project_id)['updated_at'] > '2000-01-01T00:00:00Z'


def test_delete_removes_the_row(tmp_path):
    """`delete` quita la fila; el documento no se toca aquí (lo mueve la ruta DELETE)."""
    with closing(_db(tmp_path)) as conn:
        project_id = subtitle_projects.insert(conn, 'charla', 'charla.mp4', 'out/subtitles.json')

        subtitle_projects.delete(conn, project_id)

        assert subtitle_projects.get(conn, project_id) is None
