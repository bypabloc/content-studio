"""Spec 032: el listener de la red local con TLS, apagado por defecto, y su retención del apagado por inactividad."""

from __future__ import annotations

import hashlib
import json
import socket
import ssl
import urllib.error
import urllib.request
from contextlib import closing
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from content_studio.api.app import create_app
from content_studio.db import connection
from content_studio.db import jobs as store
from content_studio.lan import cert, server
from content_studio.runtime.idle import IdleClock

ADDRESS = '127.0.0.2'


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind((ADDRESS, 0))
        return sock.getsockname()[1]


@pytest.fixture
def lan(tmp_path):
    db = tmp_path / 'content-studio.db'
    app = create_app(db, 'local-token', roots=[tmp_path / 'out'])
    clock = FakeClock()
    idle = IdleClock(minutes=1, clock=clock)
    listener = server.LanListener(db, app, idle)
    yield SimpleNamespace(db=db, app=app, clock=clock, idle=idle, listener=listener)
    listener.stop()


def _enable(lan, **extra) -> str:
    port = _free_port()
    server.write_settings(lan.db, {'enabled': True, 'address': ADDRESS, 'port': port, **extra})
    return lan.listener.apply()['url']


def _pinned(lan) -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=str(lan.db.parent / cert.CERT_NAME))
    context.check_hostname = False
    return context


def _call(url: str, context: ssl.SSLContext, token: str | None = None, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method='POST' if data else 'GET')
    if data:
        request.add_header('Content-Type', 'application/json')
    if token:
        request.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(request, context=context, timeout=10) as response:
            return response.status, json.loads(response.read() or b'null')
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b'null')


def test_ac1_off_only_loopback(lan):
    status = lan.listener.apply()

    assert status == {'running': False, 'url': None}
    with pytest.raises(OSError):
        socket.create_connection((ADDRESS, server.DEFAULTS['port']), timeout=1).close()
    assert TestClient(lan.app).get('/health', headers={'Authorization': 'Bearer local-token'}).status_code == 200


def test_ac2_tls_listener_with_fingerprint(lan):
    url = _enable(lan)
    port = int(url.rsplit(':', 1)[1])
    insecure = ssl.create_default_context()
    insecure.check_hostname = False
    insecure.verify_mode = ssl.CERT_NONE

    with socket.create_connection((ADDRESS, port), timeout=5) as raw, insecure.wrap_socket(raw) as tls:
        der = tls.getpeercert(binary_form=True)

    assert cert.format_fingerprint(hashlib.sha256(der).hexdigest()) == cert.fingerprint(lan.db.parent / cert.CERT_NAME)
    assert _call(f'{url}/health', _pinned(lan))[0] == 401
    assert _call(f'{url}/health', _pinned(lan), token='local-token')[0] == 401
    assert TestClient(lan.app).get('/health', headers={'Authorization': 'Bearer local-token'}).status_code == 200


def test_ac7_only_own_jobs(lan):
    url = _enable(lan)
    context = _pinned(lan)
    tokens = []
    for name in ('celular', 'tablet'):
        pin = lan.app.state.pairing.new()['pin']
        status, body = _call(f'{url}/pair', context, body={'pin': pin, 'name': name})
        assert status == 200
        tokens.append(body['token'])
    with closing(connection.connect(lan.db)) as conn:
        owners = [row[0] for row in conn.execute('SELECT id FROM api_clients ORDER BY id')]
        mine = store.insert(conn, 'media.convert', 'cpu', {'input': 'x'})
        store.update(conn, mine, client_id=owners[0])

    assert [job['id'] for job in _call(f'{url}/jobs', context, tokens[0])[1]] == [mine]
    assert _call(f'{url}/jobs', context, tokens[1])[1] == []
    assert _call(f'{url}/jobs/{mine}', context, tokens[1])[0] == 404


def test_ac11_keep_awake(lan):
    _enable(lan, keep_awake=True)
    lan.clock.now += 3600

    assert lan.idle.idle() is False

    server.write_settings(lan.db, {'keep_awake': False})
    lan.listener.apply()
    lan.clock.now += 3600

    assert lan.idle.idle() is True


def test_disabling_stops_the_listener(lan):
    url = _enable(lan)
    port = int(url.rsplit(':', 1)[1])

    server.write_settings(lan.db, {'enabled': False})

    assert lan.listener.apply() == {'running': False, 'url': None}
    with pytest.raises(OSError):
        socket.create_connection((ADDRESS, port), timeout=1).close()
