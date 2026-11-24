"""Proyectos (spec 020, D-3 y AC-8): agrupaciones de ítems; borrar uno no borra archivos ni ítems."""

from __future__ import annotations

from contextlib import closing

import pytest

from content_studio.db import connection, schema
from content_studio.db.connection import utc_now
from content_studio.library import projects, query


@pytest.fixture
def conn(tmp_path):
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        yield conn


def _item(conn, path: str) -> int:
    return conn.execute(
        'INSERT INTO library_items (path, kind, origin, size, mtime, media_type, indexed_at) '
        "VALUES (?, 'music', 'watched', 1, 1, 'audio', ?)",
        (path, utc_now()),
    ).lastrowid


def test_ac8_a_project_groups_items_and_filters_them(conn):
    """AC-8: el proyecto agrupa ítems (sin copiar archivos) y filtra la búsqueda."""
    first, _second = _item(conn, '/a/uno.wav'), _item(conn, '/a/dos.wav')

    project = projects.create(conn, ' Curso ')
    projects.add_items(conn, project['id'], [first, first])

    assert [(p['name'], p['count']) for p in projects.list_projects(conn)] == [('Curso', 1)]
    assert [item['name'] for item in query.search(conn, project=project['id'])['items']] == ['uno.wav']


def test_rename_remove_item_and_delete_keep_the_items(conn):
    """Renombrar, quitar un ítem y borrar el proyecto no tocan `library_items`."""
    item = _item(conn, '/a/uno.wav')
    project = projects.create(conn, 'Curso')
    projects.add_items(conn, project['id'], [item])

    assert projects.rename(conn, project['id'], 'Curso 2')['name'] == 'Curso 2'
    assert projects.remove_item(conn, project['id'], item) is True
    assert projects.delete(conn, project['id']) is True
    assert projects.delete(conn, project['id']) is False
    assert conn.execute('SELECT COUNT(*) FROM library_items').fetchone()[0] == 1


def test_invalid_names_projects_and_items_are_rejected(conn):
    """Un nombre vacío da ValueError; un proyecto o un ítem que no existe, LookupError."""
    project = projects.create(conn, 'Curso')
    with pytest.raises(ValueError):
        projects.create(conn, ' ')
    with pytest.raises(LookupError):
        projects.rename(conn, 999, 'x')
    with pytest.raises(LookupError):
        projects.add_items(conn, project['id'], [999])
    with pytest.raises(LookupError):
        projects.add_items(conn, 999, [])
