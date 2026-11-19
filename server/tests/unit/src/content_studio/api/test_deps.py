"""Conexión por petición (spec 004, D-5): `get_conn` entrega una base migrada, con claves foráneas activas."""

from __future__ import annotations

from types import SimpleNamespace

from content_studio.api.deps import get_conn
from content_studio.db import schema


def test_get_conn_yields_a_connection_to_the_app_database(tmp_path):
    db = tmp_path / 'base.db'
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_path=db)))

    gen = get_conn(request)
    conn = next(gen)
    schema.migrate(conn)

    assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
    assert db.is_file()
    gen.close()
