"""Spec 032: ajustes de la red local, direcciones privadas y el listener que no arranca si el puerto está tomado."""

from __future__ import annotations

import socket

import pytest

from content_studio.api.app import create_app
from content_studio.lan import server
from content_studio.runtime.idle import IdleClock


def test_settings_have_defaults_and_keep_changes(tmp_path):
    db = tmp_path / 'base.db'

    assert server.read_settings(db) == server.DEFAULTS
    server.write_settings(db, {'enabled': True, 'address': '192.168.1.20'})

    assert server.read_settings(db) | {} == {**server.DEFAULTS, 'enabled': True, 'address': '192.168.1.20'}


def test_private_addresses_are_ipv4_and_not_loopback():
    for address in server.private_addresses():
        assert server.valid_address(address)
        assert not address.startswith('127.')


def test_a_busy_port_is_a_lan_error(tmp_path):
    db = tmp_path / 'base.db'
    app = create_app(db, 'local', roots=[tmp_path / 'out'])
    listener = server.LanListener(db, app, IdleClock(minutes=1))
    with socket.socket() as busy:
        busy.bind(('127.0.0.2', 0))
        busy.listen()
        server.write_settings(db, {'enabled': True, 'address': '127.0.0.2', 'port': busy.getsockname()[1]})

        with pytest.raises(server.LanError):
            listener.apply()

    assert listener.status() == {'running': False, 'url': None}
    listener.stop()
