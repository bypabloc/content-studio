"""Etiquetas (spec 020, D-3 y AC-8): se crean al usarlas, se cuentan y se quitan sin tocar los archivos."""

from __future__ import annotations

from contextlib import closing

import pytest

from content_studio.db import connection, schema
from content_studio.db.connection import utc_now
from content_studio.library import query, tags


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


def test_ac8_a_tag_is_created_once_and_filters_the_item(conn):
    """AC-8: «reel 12» se crea al usarlo; el mismo nombre (con espacios de más) no se duplica."""
    first, second = _item(conn, '/a/uno.wav'), _item(conn, '/a/dos.wav')

    assert tags.add(conn, first, ' reel 12 ') == ['reel 12']
    tags.add(conn, second, 'reel 12')
    tags.add(conn, second, 'curso')

    assert tags.list_tags(conn) == [{'name': 'curso', 'count': 1}, {'name': 'reel 12', 'count': 2}]
    assert tags.remove(conn, second, 'reel 12') == ['curso']
    assert [item['name'] for item in query.search(conn, tag='reel 12')['items']] == ['uno.wav']


def test_an_empty_tag_or_an_unknown_item_is_rejected(conn):
    """Una etiqueta vacía da ValueError; un ítem que no existe, LookupError."""
    item = _item(conn, '/a/uno.wav')
    with pytest.raises(ValueError):
        tags.add(conn, item, '   ')
    with pytest.raises(LookupError):
        tags.add(conn, 999, 'reel')
