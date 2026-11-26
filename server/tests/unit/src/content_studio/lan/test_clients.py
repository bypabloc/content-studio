"""Spec 032, AC-4: un token por dispositivo, guardado como sha256, revocable; el token local no sirve en la LAN."""

from __future__ import annotations

from contextlib import closing

import pytest

from content_studio.db import connection, schema
from content_studio.lan import clients


@pytest.fixture
def conn(tmp_path):
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        yield conn


def test_ac4_no_revoked_or_local_token_is_401(conn):
    client_id, token = clients.create(conn, 'celular')

    assert clients.authenticate(conn, token)['id'] == client_id
    assert clients.authenticate(conn, '') is None
    assert clients.authenticate(conn, 'el-token-local') is None
    assert clients.revoke(conn, client_id) is True
    assert clients.authenticate(conn, token) is None
    assert clients.revoke(conn, client_id) is False


def test_the_token_is_stored_only_as_its_hash(conn):
    _, token = clients.create(conn, 'tablet')

    stored = conn.execute('SELECT token_sha256 FROM api_clients').fetchone()[0]

    assert token not in stored
    assert len(stored) == 64


def test_authenticate_marks_last_seen_and_returns_the_scopes(conn):
    _, token = clients.create(conn, 'pc', scopes=('jobs',))

    client = clients.authenticate(conn, token)

    assert client['scopes'] == ['jobs']
    assert clients.list_clients(conn)[0]['last_seen'] is not None


def test_list_hides_revoked_devices(conn):
    first, _ = clients.create(conn, 'uno')
    clients.create(conn, 'dos')
    clients.revoke(conn, first)

    assert [device['name'] for device in clients.list_clients(conn)] == ['dos']
