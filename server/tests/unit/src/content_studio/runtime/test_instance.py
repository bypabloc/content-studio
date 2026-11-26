"""Spec 028: el lock de instancia única y el arranque o parada del server compartido (runtime/instance.py)."""

import pytest

from content_studio.runtime import discovery, instance

INFO = {'url': 'http://127.0.0.1:41830', 'port': 41830, 'pid': 1, 'version': '0.1.0'}


def test_hold_lock_is_exclusive(tmp_path):
    with instance.hold_lock(tmp_path), pytest.raises(instance.AlreadyRunning), instance.hold_lock(tmp_path):
        pass
    with instance.hold_lock(tmp_path):
        pass


def test_alive_is_false_without_server():
    assert instance.alive({'url': 'http://127.0.0.1:9'}, 'token', timeout=0.5) is False


def test_ensure_running_reuses_live_server(tmp_path, monkeypatch):
    discovery.write(tmp_path, INFO)
    monkeypatch.setattr(instance, 'alive', lambda info, token, timeout=2: True)
    launched: list[object] = []
    monkeypatch.setattr(instance, '_launch', lambda db, port: launched.append(port))
    assert instance.ensure_running(tmp_path / 'base.db') == INFO
    assert launched == []


def test_ensure_running_starts_when_none(tmp_path, monkeypatch):
    monkeypatch.setattr(instance, '_launch', lambda db, port: discovery.write(tmp_path, INFO))
    monkeypatch.setattr(instance, 'alive', lambda info, token, timeout=2: True)
    assert instance.ensure_running(tmp_path / 'base.db', timeout=5) == INFO


def test_ensure_running_gives_up_when_nobody_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(instance, '_launch', lambda db, port: None)
    with pytest.raises(TimeoutError):
        instance.ensure_running(tmp_path / 'base.db', timeout=0.3)


def test_stop_without_server_returns_false(tmp_path):
    assert instance.stop(tmp_path) is False
