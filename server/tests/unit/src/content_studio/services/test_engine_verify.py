"""Trabajo engine.verify, su resultado y el registro de la API/cola."""

import sys

from content_studio.db import connection, schema, settings
from content_studio.services.registry import SERVICES


def test_engine_verify_is_registered_as_a_gpu_service():
    assert 'engine.verify' in SERVICES
    service = SERVICES['engine.verify']
    assert service.RESOURCE == 'gpu'
    assert service.ERROR_CODES[31] == 'engine_verify_failed'


def test_validate_and_build_command(tmp_path):
    from content_studio.services import engine_verify

    assert engine_verify.validate({'engine': 'qwen-0.6b'}) == []
    assert engine_verify.validate({'engine': 'unknown'})[0]['code'] == 'unknown_engine'
    assert engine_verify.build_command({'engine': 'qwen-0.6b'}, tmp_path) == [
        sys.executable,
        '-m',
        'content_studio.services.engine_verify',
        'qwen-0.6b',
        str(tmp_path),
    ]


def test_failed_verification_is_saved_for_engines_page(tmp_path, monkeypatch):
    from content_studio.services import engine_verify

    database = tmp_path / 'jobs.db'
    conn = connection.connect(database)
    schema.migrate(conn)
    conn.close()
    result = {'ok': False, 'error': 'model failed', 'checked_at': '2026-11-21T00:00:00+00:00'}
    monkeypatch.setattr(engine_verify.paths, 'db_path', lambda: database)
    monkeypatch.setattr(engine_verify.verification, 'verify_engine', lambda engine, output: result)

    assert engine_verify.run('qwen-0.6b', tmp_path / 'verify') == 31

    conn = connection.connect(database)
    assert settings.get(conn, 'engine.verify.qwen-0.6b') == result
    conn.close()


def test_missing_engine_uses_its_error_code(tmp_path, monkeypatch):
    from content_studio.services import engine_verify

    database = tmp_path / 'jobs.db'
    conn = connection.connect(database)
    schema.migrate(conn)
    conn.close()
    result = {'ok': False, 'error': 'engine_not_installed', 'checked_at': '2026-11-21T00:00:00+00:00'}
    monkeypatch.setattr(engine_verify.paths, 'db_path', lambda: database)
    monkeypatch.setattr(engine_verify.verification, 'verify_engine', lambda engine, output: result)

    assert engine_verify.run('qwen-0.6b', tmp_path / 'verify') == 30

    conn = connection.connect(database)
    assert settings.get(conn, 'engine.verify.qwen-0.6b') == result
    conn.close()
