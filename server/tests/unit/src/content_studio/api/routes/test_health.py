"""Salud de la API (spec 004, D-5): responde con el token válido."""

from __future__ import annotations


def test_health_answers_ok_with_the_token(api):
    response = api.client.get('/health', headers=api.headers)

    assert response.status_code == 200
    assert response.json() == {'ok': True}
