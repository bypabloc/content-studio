"""Spec 032, AC-8: la puerta del MCP de la red local valida el Origin y el token, y deja el token al puente."""

from __future__ import annotations

from contextlib import closing

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from content_studio.db import connection, schema
from content_studio.lan import clients, mcp_http

ORIGIN = 'https://127.0.0.2:41831'


def _client(tmp_path) -> tuple[TestClient, str]:
    db = tmp_path / 'base.db'
    with closing(connection.connect(db)) as conn:
        schema.migrate(conn)
        _, token = clients.create(conn, 'celular')

    async def inner(scope, receive, send):
        await PlainTextResponse(mcp_http.current_token.get())(scope, receive, send)

    app = Starlette(routes=[Route('/mcp', endpoint=mcp_http.DeviceGate(inner, db, ORIGIN), methods=['POST'])])
    return TestClient(app), token


def test_the_device_token_reaches_the_mcp(tmp_path):
    client, token = _client(tmp_path)

    response = client.post('/mcp', headers={'Authorization': f'Bearer {token}', 'Origin': ORIGIN})

    assert response.text == token


def test_a_foreign_origin_is_403(tmp_path):
    client, token = _client(tmp_path)

    response = client.post('/mcp', headers={'Authorization': f'Bearer {token}', 'Origin': 'https://evil.example'})

    assert response.status_code == 403
    assert response.json()['code'] == 'origin_not_allowed'


def test_without_a_device_it_is_401(tmp_path):
    client, _ = _client(tmp_path)

    response = client.post('/mcp', headers={'Authorization': 'Bearer local-token', 'Accept-Language': 'en'})

    assert response.status_code == 401
    assert response.json()['code'] == 'unauthorized'


def test_a_device_without_jobs_is_401(tmp_path):
    client, _ = _client(tmp_path)
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        _, token = clients.create(conn, 'solo archivos', scopes=('files',))

    assert client.post('/mcp', headers={'Authorization': f'Bearer {token}'}).status_code == 401
