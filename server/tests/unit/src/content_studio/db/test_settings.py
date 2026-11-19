"""Tabla `settings` (spec 004, D-1): preferencias por clave, con valor JSON."""

from __future__ import annotations

import pytest

from content_studio.db import connection, schema, settings


@pytest.fixture
def conn(tmp_path):
    db = connection.connect(tmp_path / 'base.db')
    schema.migrate(db)
    yield db
    db.close()


def test_missing_key_returns_the_default(conn):
    assert settings.get(conn, 'narration.model') is None
    assert settings.get(conn, 'narration.model', 'qwen-0.6b') == 'qwen-0.6b'


def test_set_then_get_round_trips_json_values(conn):
    settings.set_value(conn, 'narration.model', 'qwen-0.6b')
    settings.set_value(conn, 'queue.paused', True)

    assert settings.get(conn, 'narration.model') == 'qwen-0.6b'
    assert settings.get(conn, 'queue.paused') is True


def test_set_overwrites_the_previous_value(conn):
    settings.set_value(conn, 'narration.model', 'qwen-0.6b')
    settings.set_value(conn, 'narration.model', 'cosyvoice3')

    assert settings.get(conn, 'narration.model') == 'cosyvoice3'
    assert settings.all_values(conn) == {'narration.model': 'cosyvoice3'}
