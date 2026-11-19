"""`studio serve` (spec 004, D-5): una línea `ready` con el puerto (y el token si lo generó) cuando la API escucha."""

from __future__ import annotations

from content_studio.cli import serve


def test_ready_line_is_one_json_line_with_the_port():
    assert serve.ready_line(8765) == '{"ready": {"port": 8765}}'


def test_ready_line_adds_the_token_when_the_server_generated_it():
    assert serve.ready_line(8765, 'abc') == '{"ready": {"port": 8765, "token": "abc"}}'


def test_pick_free_port_returns_a_port_that_can_be_bound():
    port = serve.pick_free_port()

    assert 0 < port < 65536
