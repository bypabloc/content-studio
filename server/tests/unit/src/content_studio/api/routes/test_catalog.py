"""Catálogo de la API (spec 004, D-5, AC-8): cada selector tiene exactamente una opción recomendada."""

from __future__ import annotations

import json

from content_studio import paths


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


def test_profiles_are_listed_with_the_styles_each_one_has(api, monkeypatch, tmp_path):
    refs = tmp_path / 'reference'
    monkeypatch.setattr(paths, 'REFERENCE', refs)
    (refs / 'default').mkdir(parents=True)
    (refs / 'default/expert.wav').write_bytes(b'RIFF')
    (refs / 'default/profile.json').write_text(json.dumps({'name': 'Mi voz'}), encoding='utf-8')

    body = api.client.get('/catalog/narration', headers=api.headers).json()

    assert body['profiles'] == [{'id': 'default', 'name': 'Mi voz', 'styles': ['expert']}]
