"""Caché de transcripciones (spec 013, D-4 y AC-6): la base guarda rutas y metadatos, nunca el texto."""

from __future__ import annotations

import pytest

from content_studio.db import schema
from content_studio.db.connection import connect
from content_studio.transcription import cache


@pytest.fixture
def conn(tmp_path):
    database = connect(tmp_path / 'content-studio.db')
    schema.migrate(database)
    return database


def _json(tmp_path, name: str = 'words.json'):
    path = tmp_path / name
    path.write_text('{"segments": []}', encoding='utf-8')
    return path


def test_ac6_the_same_file_model_and_language_hit_the_cache(conn, tmp_path):
    """AC-6: un archivo ya transcrito con el mismo modelo e idioma encuentra su JSON; no se vuelve a transcribir."""
    json_path = _json(tmp_path)
    cache.store(conn, '/media/a.mp4', 1.5, 100, 'small', 'es', str(json_path))

    assert cache.find(conn, '/media/a.mp4', 1.5, 100, 'small', 'es') == str(json_path)


def test_ac6_another_model_or_language_misses_the_cache(conn, tmp_path):
    """AC-6: con otro modelo o idioma, no hay acierto."""
    cache.store(conn, '/media/a.mp4', 1.5, 100, 'small', 'es', str(_json(tmp_path)))

    assert cache.find(conn, '/media/a.mp4', 1.5, 100, 'medium', 'es') is None
    assert cache.find(conn, '/media/a.mp4', 1.5, 100, 'small', 'en') is None


def test_ac6_a_changed_file_misses_the_cache(conn, tmp_path):
    """Si el archivo cambió (mtime o tamaño), la transcripción vieja no sirve."""
    cache.store(conn, '/media/a.mp4', 1.5, 100, 'small', 'es', str(_json(tmp_path)))

    assert cache.find(conn, '/media/a.mp4', 2.0, 100, 'small', 'es') is None
    assert cache.find(conn, '/media/a.mp4', 1.5, 101, 'small', 'es') is None


def test_ac6_a_missing_json_file_is_a_miss(conn, tmp_path):
    """Si el JSON se borró, la fila sola no basta: no hay acierto."""
    json_path = _json(tmp_path)
    cache.store(conn, '/media/a.mp4', 1.5, 100, 'small', 'es', str(json_path))
    json_path.unlink()

    assert cache.find(conn, '/media/a.mp4', 1.5, 100, 'small', 'es') is None


def test_ac6_the_database_keeps_the_path_and_no_content(conn):
    """AC-6: la tabla `transcripts` guarda la ruta del JSON y metadatos; no hay columnas BLOB ni de texto."""
    columns = {row['name']: row['type'] for row in conn.execute('PRAGMA table_info(transcripts)')}

    assert 'json_path' in columns
    assert all(kind.upper() != 'BLOB' for kind in columns.values())
    assert not {'text', 'content', 'words'} & set(columns)


def test_cache_key_changes_with_the_path_mtime_model_and_language():
    """La clave es un sha1 de ruta, mtime, modelo e idioma: cualquier cambio da otra clave."""
    base = cache.cache_key('/media/a.mp4', 1.5, 'small', 'es')

    assert len(base) == 40
    assert cache.cache_key('/media/a.mp4', 1.5, 'small', 'es') == base
    assert cache.cache_key('/media/b.mp4', 1.5, 'small', 'es') != base
    assert cache.cache_key('/media/a.mp4', 2.5, 'small', 'es') != base
    assert cache.cache_key('/media/a.mp4', 1.5, 'medium', 'es') != base
    assert cache.cache_key('/media/a.mp4', 1.5, 'small', 'en') != base


def test_json_path_lives_under_the_data_dir_transcripts_folder(tmp_path, monkeypatch):
    """Los JSON de transcripción van en `<datos>/transcripts/<clave>.json`."""
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(tmp_path))

    assert cache.json_path('abc') == tmp_path / 'transcripts' / 'abc.json'
