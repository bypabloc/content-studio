"""devtools app-check: la carpeta y el entorno aislados de una corrida (spec 024, AC-4 y AC-9)."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pytest

from devtools.app_check import env

NOW = datetime(2026, 11, 22, 16, 30, 5)


def settings_of(db: Path) -> dict[str, str]:
    with closing(sqlite3.connect(db)) as conn:
        return dict(conn.execute('SELECT key, value FROM settings'))


def test_ac4_temp_run_isolates_webview_home_db_and_target(tmp_path):
    run = env.prepare(tmp_path, 'temp', NOW)
    assert run.dir == tmp_path / 'tmp/app-check/20261122-163005'
    assert run.env['WEBVIEW2_USER_DATA_FOLDER'] == str(run.dir / 'webview2')
    assert run.env['CONTENT_STUDIO_HOME'] == str(run.dir / 'home')
    assert run.env['CONTENT_STUDIO_DB'] == str(run.dir / 'content-studio.db')
    assert run.env['CARGO_TARGET_DIR'] == str(tmp_path / 'tmp/app-check/cargo-target')
    assert run.env['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] == f'--remote-debugging-port={run.port}'
    assert 1024 < run.port < 65536
    # Las salidas de la corrida tampoco caen en out/ del worktree.
    fresh = settings_of(run.dir / 'content-studio.db')
    assert fresh['storage.outputs'] == f'"{(run.dir / "out").as_posix()}"'
    assert fresh['welcome.done'] == 'true'
    assert (run.dir / 'shots').is_dir()


def test_ac4_prepare_does_not_touch_the_process_environment(tmp_path, monkeypatch):
    monkeypatch.delenv('CONTENT_STUDIO_HOME', raising=False)
    env.prepare(tmp_path, 'temp', NOW)
    import os

    assert 'CONTENT_STUDIO_HOME' not in os.environ


def test_ac9_real_run_copies_db_and_pauses_queue(tmp_path):
    source = tmp_path / 'user.db'
    with closing(sqlite3.connect(source)) as conn, conn:
        env.migrate(conn)
        conn.execute("INSERT INTO settings (key, value, updated_at) VALUES ('storage.outputs', '\"D:/out\"', 'x')")
    before = (hashlib.sha256(source.read_bytes()).hexdigest(), source.stat().st_mtime_ns)
    run = env.prepare(tmp_path, 'real', NOW, source_db=source)
    assert run.db == 'copy'
    assert 'CONTENT_STUDIO_HOME' not in run.env
    copy = Path(run.env['CONTENT_STUDIO_DB'])
    assert copy == run.dir / 'content-studio.db'
    copied = settings_of(copy)
    assert copied['queue.paused'] == 'true'
    assert copied['storage.outputs'] == '"D:/out"'
    assert (hashlib.sha256(source.read_bytes()).hexdigest(), source.stat().st_mtime_ns) == before
    assert 'queue.paused' not in settings_of(source)


def test_ac4_real_run_without_db_starts_a_fresh_paused_db_with_the_user_outputs(tmp_path):
    outputs = tmp_path / 'user-out'
    outputs.mkdir()
    run = env.prepare(tmp_path, 'real', NOW, source_db=tmp_path / 'missing.db', outputs=outputs)
    assert run.db == 'fresh'
    assert 'CONTENT_STUDIO_HOME' not in run.env
    fresh = settings_of(Path(run.env['CONTENT_STUDIO_DB']))
    assert fresh['queue.paused'] == 'true'
    assert fresh['storage.outputs'] == f'"{outputs.as_posix()}"'
    assert not (tmp_path / 'missing.db').exists()


def test_ac4_unknown_data_mode_is_an_error(tmp_path):
    with pytest.raises(env.AppCheckError, match='--data'):
        env.prepare(tmp_path, 'prod', NOW)


def test_free_port_is_bindable():
    import socket

    with socket.socket() as sock:
        sock.bind(('127.0.0.1', env.free_port()))
