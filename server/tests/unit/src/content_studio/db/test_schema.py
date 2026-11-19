"""Migraciones de la base (spec 004, D-1 y AC-1): idempotentes, con `jobs` y `settings`, y sin columnas BLOB."""

from __future__ import annotations

from contextlib import closing

from content_studio.db import connection, schema


def _tables(conn) -> set[str]:
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_ac1_migrate_twice_sets_version_1_and_creates_tables(tmp_path):
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        schema.migrate(conn)

        assert conn.execute('PRAGMA user_version').fetchone()[0] == 1
        assert {'jobs', 'settings'} <= _tables(conn)


def test_no_blob_columns(tmp_path):
    """La base solo guarda metadatos: ninguna columna puede ser BLOB (decisión del usuario, spec 004, D-1)."""
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        columns = [
            (table, col[1], col[2]) for table in _tables(conn) for col in conn.execute(f'PRAGMA table_info({table})')
        ]

    assert columns, 'sin columnas: la prueba no mide nada'
    assert [item for item in columns if 'BLOB' in (item[2] or '').upper()] == []
