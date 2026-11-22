"""Tabla `mix_projects` (spec 016, D-3): la base guarda nombre y ruta; el documento vive en disco."""

from __future__ import annotations

from contextlib import closing

from content_studio.db import connection, mix_projects, schema


def _db(tmp_path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    return conn


def test_insert_gives_an_id_and_get_reads_the_name_back(tmp_path):
    """El id que devuelve `insert` es el de la fila, y `get` lee el nombre sin cambios."""
    with closing(_db(tmp_path)) as conn:
        project_id = mix_projects.insert(conn, 'charla', '')

        project = mix_projects.get(conn, project_id)

    assert (project['id'], project['name'], project['doc_path']) == (project_id, 'charla', '')


def test_set_doc_path_fixes_the_document_path_once_the_folder_exists(tmp_path):
    """`set_doc_path` guarda la ruta del `mix.json` cuando su carpeta ya tiene id."""
    with closing(_db(tmp_path)) as conn:
        project_id = mix_projects.insert(conn, 'charla', '')

        mix_projects.set_doc_path(conn, project_id, 'out/mix/2026-11-22-1/mix.json')

        assert mix_projects.get(conn, project_id)['doc_path'] == 'out/mix/2026-11-22-1/mix.json'


def test_touch_moves_updated_at(tmp_path):
    """`touch` deja `updated_at` en el momento de la llamada."""
    with closing(_db(tmp_path)) as conn:
        project_id = mix_projects.insert(conn, 'charla', '')
        conn.execute("UPDATE mix_projects SET updated_at = '2000-01-01T00:00:00Z' WHERE id = ?", (project_id,))

        mix_projects.touch(conn, project_id)

        assert mix_projects.get(conn, project_id)['updated_at'] > '2000-01-01T00:00:00Z'


def test_get_returns_none_for_a_missing_project(tmp_path):
    """Un id que no existe no devuelve fila."""
    with closing(_db(tmp_path)) as conn:
        assert mix_projects.get(conn, 999) is None
