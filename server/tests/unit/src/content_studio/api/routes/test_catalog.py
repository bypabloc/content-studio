"""Catálogo de la API (spec 004, D-5, AC-8): cada selector tiene exactamente una opción recomendada."""

from __future__ import annotations


def test_ac8_each_narration_selector_has_exactly_one_recommended_option(api):
    body = api.client.get('/catalog/narration', headers=api.headers).json()

    assert sum(engine['recommended'] for engine in body['engines']) == 1
    assert sum(style['recommended'] for style in body['styles']) == 1
    assert {'id', 'license', 'commercial', 'installed', 'recommended'} <= set(body['engines'][0])


def test_ac8_each_music_selector_has_exactly_one_recommended_option(api):
    body = api.client.get('/catalog/music', headers=api.headers).json()

    assert sum(model['recommended'] for model in body['models']) == 1
    assert sum(style['recommended'] for style in body['styles']) == 1
    assert len(body['styles']) > 100


def test_an_unknown_catalog_is_404(api):
    assert api.client.get('/catalog/nope', headers=api.headers).status_code == 404
