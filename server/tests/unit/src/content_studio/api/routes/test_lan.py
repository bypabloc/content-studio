"""Spec 032: rutas locales de la red local (solo 127.0.0.1): PIN, dispositivos y ajustes."""

from __future__ import annotations

from contextlib import closing

from content_studio.db import connection
from content_studio.lan import clients


def test_pairing_creates_a_pin_in_the_shared_pairing(api):
    body = api.client.post('/lan/pairing', headers=api.headers).json()

    api.app.state.pairing.redeem(body['pin'])
    assert body['expires_in'] > 0


def test_devices_are_listed_and_revoked(api):
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        client_id, _ = clients.create(conn, 'celular')

    listed = api.client.get('/lan/devices', headers=api.headers).json()
    revoked = api.client.delete(f'/lan/devices/{client_id}', headers=api.headers)
    again = api.client.delete(f'/lan/devices/{client_id}', headers=api.headers)

    assert [device['name'] for device in listed] == ['celular']
    assert revoked.status_code == 204
    assert again.status_code == 404
    assert api.client.get('/lan/devices', headers=api.headers).json() == []


def test_settings_start_off_with_the_defaults(api):
    body = api.client.get('/lan/settings', headers=api.headers).json()

    assert body['enabled'] is False
    assert body['port'] == 41831
    assert body['running'] is False
    assert body['fingerprint'] is None
    assert isinstance(body['addresses'], list)


def test_settings_reject_a_public_address(api):
    response = api.client.put('/lan/settings', json={'address': '8.8.8.8'}, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'lan_address_invalid'


def test_settings_are_saved_without_a_listener(api):
    body = api.client.put(
        '/lan/settings', json={'address': '127.0.0.2', 'max_upload_mb': 10, 'keep_awake': False}, headers=api.headers
    ).json()

    assert body['address'] == '127.0.0.2'
    assert body['max_upload_mb'] == 10
    assert body['keep_awake'] is False


def test_enabling_without_any_address_is_422(api, monkeypatch):
    monkeypatch.setattr('content_studio.lan.server.private_addresses', lambda: [])

    response = api.client.put('/lan/settings', json={'enabled': True}, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'lan_no_address'


def test_lan_routes_need_the_local_token(api):
    assert api.client.get('/lan/settings').status_code == 401
