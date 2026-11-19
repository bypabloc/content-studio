"""Ajustes de la API (spec 004, D-5, AC-8): lo que se guarda con PUT se devuelve con GET."""

from __future__ import annotations


def test_ac8_a_put_setting_is_returned_by_get(api):
    assert api.client.get('/settings/narration.model', headers=api.headers).json() == {
        'key': 'narration.model',
        'value': None,
    }

    api.client.put('/settings/narration.model', json={'value': 'voxcpm2'}, headers=api.headers)

    assert api.client.get('/settings/narration.model', headers=api.headers).json()['value'] == 'voxcpm2'
