"""Ajustes de la API (spec 004, D-5, AC-8): lo que se guarda con PUT se devuelve con GET."""

from __future__ import annotations


def test_ac8_a_put_setting_is_returned_by_get(api):
    assert api.client.get('/settings/narration.model', headers=api.headers).json() == {
        'key': 'narration.model',
        'value': None,
    }

    api.client.put('/settings/narration.model', json={'value': 'voxcpm2'}, headers=api.headers)

    assert api.client.get('/settings/narration.model', headers=api.headers).json()['value'] == 'voxcpm2'


def test_ac4_delete_prefix_resets_the_selectors_and_keeps_ui_and_notify(api):
    for key, value in [
        ('select.narration.model', 'x'),
        ('select.music.model', 'y'),
        ('ui.theme', 'dark'),
        ('notify.sound', False),
    ]:
        api.client.put(f'/settings/{key}', json={'value': value}, headers=api.headers)

    response = api.client.delete('/settings', params={'prefix': 'select.'}, headers=api.headers)

    assert response.status_code == 200
    assert response.json() == {'deleted': 2}
    assert api.client.get('/settings/select.music.model', headers=api.headers).json()['value'] is None
    assert api.client.get('/settings/ui.theme', headers=api.headers).json()['value'] == 'dark'
    assert api.client.get('/settings/notify.sound', headers=api.headers).json()['value'] is False


def test_delete_refuses_a_prefix_outside_the_selectors(api):
    response = api.client.delete('/settings', params={'prefix': 'ui.'}, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'invalid_prefix'
