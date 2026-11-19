"""`studio serve` (spec 004, D-5): una línea `ready` con el puerto (y el token si lo generó) cuando la API escucha."""

from __future__ import annotations

import json

from content_studio.cli import serve


class _FakeWorker:
    def __init__(self, db, main, publish) -> None:
        self.publish = publish

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


class _FakeServer:
    def __init__(self, config) -> None:
        self.started = True
        self.should_exit = False

    def run(self) -> None:
        pass


def _serve_with_fakes(monkeypatch, tmp_path, port, token) -> int:
    monkeypatch.setattr(serve, 'Worker', _FakeWorker)
    monkeypatch.setattr(serve.uvicorn, 'Server', _FakeServer)
    return serve.serve(tmp_path / 'base.db', tmp_path, port, token)


def test_ready_line_is_one_json_line_with_the_port():
    assert serve.ready_line(8765) == '{"ready": {"port": 8765}}'


def test_ready_line_adds_the_token_when_the_server_generated_it():
    assert serve.ready_line(8765, 'abc') == '{"ready": {"port": 8765, "token": "abc"}}'


def test_pick_free_port_returns_a_port_that_can_be_bound():
    port = serve.pick_free_port()

    assert 0 < port < 65536


def test_serve_prints_ready_with_the_token_it_generated(monkeypatch, tmp_path, capsys):
    assert _serve_with_fakes(monkeypatch, tmp_path, 9, None) == 0

    ready = json.loads(capsys.readouterr().out)['ready']
    assert ready['port'] == 9
    assert len(ready['token']) >= 32


def test_serve_does_not_print_the_token_it_was_given(monkeypatch, tmp_path, capsys):
    assert _serve_with_fakes(monkeypatch, tmp_path, 9, 'mi-token') == 0

    assert json.loads(capsys.readouterr().out) == {'ready': {'port': 9}}
