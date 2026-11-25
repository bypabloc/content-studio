"""Spec 028, AC-1 a AC-3: `studio api up` arranca un server compartido, lo reutiliza y evita un puerto ocupado."""

import socket
import threading

import pytest

from content_studio.runtime import discovery, instance


@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    db = tmp_path / 'content-studio.db'
    yield db
    instance.stop(db.parent)


def test_ac1_up_starts_and_writes_api_json(base):
    info = instance.ensure_running(base, timeout=90)
    assert discovery.read(base.parent)['pid'] == info['pid']
    assert instance.alive(info, discovery.token(base.parent))


def test_ac2_two_up_one_server(base):
    results: list[dict] = []
    threads = [
        threading.Thread(target=lambda: results.append(instance.ensure_running(base, timeout=90))) for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(results) == 2
    assert len({result['pid'] for result in results}) == 1
    assert len({result['url'] for result in results}) == 1


def test_ac3_busy_port_uses_another(base, tmp_path):
    busy = socket.socket()
    busy.bind(('127.0.0.1', 0))
    busy.listen()
    port = busy.getsockname()[1]
    try:
        info = instance.ensure_running(base, timeout=90, port=port)
    finally:
        busy.close()
    assert info['port'] != port
    assert discovery.read(base.parent)['port'] == info['port']
    assert str(port) in (tmp_path / 'home' / 'logs' / 'server.log').read_text(encoding='utf-8')
