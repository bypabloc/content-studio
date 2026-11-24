"""Migraciones de la base (spec 004, D-1 y AC-1): idempotentes, con `jobs` y `settings`, y sin columnas BLOB."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from content_studio.db import connection, schema


def _tables(conn) -> set[str]:
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_ac1_migrate_twice_sets_version_8_and_creates_tables(tmp_path):
    """La 8 suma `publish_path` (021); la 7, la biblioteca (020); la 6, `mix_projects` (016); la 5,
    `subtitle_projects` (014); la 4, la caché."""
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        schema.migrate(conn)

        assert conn.execute('PRAGMA user_version').fetchone()[0] == 8
        assert 'publish_path' in {row[1] for row in conn.execute('PRAGMA table_info(library_items)')}
        assert {'jobs', 'settings', 'transcripts', 'subtitle_projects', 'mix_projects'} <= _tables(conn)
        library = {'library_items', 'library_folders', 'tags', 'item_tags', 'projects', 'project_items'}
        assert library <= _tables(conn)


def test_library_items_have_indexes_for_path_kind_and_mtime(tmp_path):
    """AC-9 (spec 020): la búsqueda por nombre, tipo y fecha usa índices SQL."""
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        indexed = {
            row[2]
            for name in ('library_items_kind', 'library_items_mtime')
            for row in conn.execute(f'PRAGMA index_info({name})')
        }

    assert indexed == {'kind', 'mtime'}


def test_no_blob_columns(tmp_path):
    """La base solo guarda metadatos: ninguna columna puede ser BLOB (decisión del usuario, spec 004, D-1)."""
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        columns = [
            (table, col[1], col[2]) for table in _tables(conn) for col in conn.execute(f'PRAGMA table_info({table})')
        ]

    assert columns, 'sin columnas: la prueba no mide nada'
    assert [item for item in columns if 'BLOB' in (item[2] or '').upper()] == []


def test_jobs_have_the_starred_flag_and_the_group_key(tmp_path):
    """Migración 3 (spec 006, D-4): `starred` y `group_key` en `jobs`."""
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        columns = {row[1] for row in conn.execute('PRAGMA table_info(jobs)')}

    assert {'starred', 'group_key'} <= columns


def _old_base(path, version):
    """Una base de una versión anterior: las primeras `version` migraciones y un trabajo guardado."""
    with closing(connection.connect(path)) as conn:
        for number, sql in enumerate(schema.MIGRATIONS[:version], start=1):
            conn.executescript(f'BEGIN;\n{sql}\nPRAGMA user_version = {number};\nCOMMIT;')
        conn.execute("INSERT INTO settings (key, value, updated_at) VALUES ('ui.theme', '\"dark\"', '2026-11-24')")
        conn.commit()


def test_ac3_backup_restore(tmp_path, monkeypatch):
    """Spec 022, AC-3: antes de migrar queda un respaldo en backups/; si una migración falla, la base vuelve a él."""
    base, backups = tmp_path / 'base.db', tmp_path / 'backups'
    _old_base(base, 7)

    with closing(connection.connect(base)) as conn:
        schema.migrate(conn, backups)
        assert conn.execute('PRAGMA user_version').fetchone()[0] == len(schema.MIGRATIONS)
    copies = list(backups.glob('*-v7.db'))
    assert len(copies) == 1
    with closing(connection.connect(copies[0])) as old:
        assert old.execute('PRAGMA user_version').fetchone()[0] == 7

    monkeypatch.setattr(schema, 'MIGRATIONS', [*schema.MIGRATIONS, 'CREATE TABLE settings (x);'])
    with closing(connection.connect(base)) as conn, pytest.raises(sqlite3.Error):
        schema.migrate(conn, backups)
    with closing(connection.connect(base)) as conn:
        assert conn.execute('PRAGMA user_version').fetchone()[0] == len(schema.MIGRATIONS) - 1
        assert conn.execute("SELECT value FROM settings WHERE key = 'ui.theme'").fetchone()[0] == '"dark"'


def test_only_the_last_five_backups_are_kept(tmp_path, monkeypatch):
    """La carpeta de respaldos no crece sin fin: quedan los 5 más nuevos."""
    base, backups = tmp_path / 'base.db', tmp_path / 'backups'
    backups.mkdir()
    for day in range(1, 7):
        (backups / f'2026-11-0{day}-000000-v1.db').write_bytes(b'')
    _old_base(base, 7)

    with closing(connection.connect(base)) as conn:
        schema.migrate(conn, backups)

    names = sorted(path.name for path in backups.glob('*.db'))
    assert len(names) == 5 and names[-1].endswith('-v7.db') and '2026-11-01-000000-v1.db' not in names


def test_a_new_base_needs_no_backup(tmp_path):
    """Una base vacía (versión 0) no tiene nada que respaldar."""
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn, tmp_path / 'backups')
    assert not (tmp_path / 'backups').exists()
