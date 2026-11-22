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


def test_the_media_catalog_lists_the_formats_and_one_recommended_preset_for_the_aspect(api):
    """Convertir: cada formato con su tipo, y exactamente un preset de red ★ según la proporción de la fuente (D-2)."""
    body = api.client.get('/catalog/media', params={'aspect': 0.5625}, headers=api.headers).json()

    assert {'id': 'mp3', 'kind': 'audio'} in body['formats']
    assert {'id': 'gif', 'kind': 'gif'} in body['formats']
    assert sum(preset['recommended'] for preset in body['presets']) == 1
    recommended = next(preset for preset in body['presets'] if preset['recommended'])
    assert (recommended['id'], recommended['width'], recommended['height']) == ('reels', 1080, 1920)


def test_the_media_catalog_recommends_the_landscape_preset_for_a_wide_source(api):
    body = api.client.get('/catalog/media', params={'aspect': 1.7778}, headers=api.headers).json()

    assert next(preset for preset in body['presets'] if preset['recommended'])['id'] == 'youtube-1080'
