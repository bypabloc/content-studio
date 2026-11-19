"""Conexión a la base (spec 004, D-1): carpeta creada, WAL, claves foráneas y espera ante bloqueos."""

from __future__ import annotations

from contextlib import closing

from content_studio.db import connection


def test_connect_creates_folder_and_sets_wal_foreign_keys_and_busy_timeout(tmp_path):
    with closing(connection.connect(tmp_path / 'sub' / 'base.db')) as conn:
        assert conn.execute('PRAGMA journal_mode').fetchone()[0] == 'wal'
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        assert conn.execute('PRAGMA busy_timeout').fetchone()[0] == 5000
