"""Token de la API (spec 004, D-5, AC-6): cada ruta exige el Bearer; el `?token=` solo vale en /files y /events."""

from __future__ import annotations


def test_ac6_every_endpoint_needs_the_bearer_token(api):
    assert api.client.get('/health').status_code == 401
    assert api.client.get('/health', headers={'Authorization': 'Bearer otro'}).status_code == 401
    assert api.client.get('/health', headers=api.headers).status_code == 200


def test_query_token_is_not_accepted_outside_files_and_events(api):
    assert api.client.get('/health', params={'token': api.token}).status_code == 401


def test_the_401_body_has_a_code_and_a_message(api):
    body = api.client.get('/health').json()

    assert body['code'] == 'unauthorized'
    assert body['message']
