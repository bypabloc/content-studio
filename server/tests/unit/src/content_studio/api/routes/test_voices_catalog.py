"""Catálogo de voces libres en la API (spec 010, D-5, AC-7 y AC-9): ficha, estado de cada voz y favoritas."""

from __future__ import annotations

import json

import pytest

from content_studio import paths
from content_studio.narration.styles import STYLES
from content_studio.narration.voices import catalog as voice_catalog

SHEET = {
    'language': 'es',
    'license': 'CC0',
    'description': 'femenina, grabación casera',
    'source': 'Kyutai tts-voices',
    'rights': 'CC0-1.0',
    'consent': True,
}


def _build(root, name, styles):
    """Una construcción en `root/name`: un WAV por estilo y la aprobación de cada uno de `styles`."""
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    for style in styles:
        (folder / f'{style}.wav').write_bytes(b'')
    results = {style: {'ok': True} for style in styles}
    (folder / 'aprobacion.json').write_text(json.dumps({'styles': results}), encoding='utf-8')


@pytest.fixture
def voices(api, monkeypatch):
    """Catálogo de dos voces en una carpeta temporal: `ana` sin construir y `luis` aprobada en los 12 estilos."""
    root = api.tmp / 'voices'
    root.mkdir()
    monkeypatch.setattr(paths, 'ROOT', api.tmp)  # las muestras que da la API son relativas a la raíz, como /files
    (root / 'catalog.json').write_text(json.dumps({'ana': SHEET, 'luis': SHEET}), encoding='utf-8')
    monkeypatch.setattr(paths, 'VOICES', root)
    monkeypatch.setattr(voice_catalog, 'CATALOG', root / 'catalog.json')
    _build(root, 'luis', STYLES)
    return root


def _card(api, name):
    """La ficha de una voz en `GET /voices/catalog`."""
    body = api.client.get('/voices/catalog', headers=api.headers).json()
    return next(voice for voice in body['voices'] if voice['id'] == name)


def test_ac7_a_voice_that_was_never_built_is_not_built(api, voices):
    assert _card(api, 'ana')['state'] == 'not_built'


def test_ac7_a_voice_approved_in_every_style_is_approved_and_lists_each_style(api, voices):
    card = _card(api, 'luis')

    assert card['state'] == 'approved'
    assert [item['style'] for item in card['styles']] == list(STYLES)
    assert all(item['approved'] for item in card['styles'])


def test_ac7_a_build_with_some_styles_rejected_is_partial(api, voices):
    _build(voices, 'ana', ['expert', 'neutral'])

    card = _card(api, 'ana')

    assert card['state'] == 'partial'
    assert sum(item['approved'] for item in card['styles']) == 2


def test_the_card_carries_the_sheet_and_the_license(api, voices):
    card = _card(api, 'luis')

    assert card['license'] == 'CC0' and card['source'] == 'Kyutai tts-voices' and card['consent'] is True


def test_ac9_the_favorites_come_from_settings_and_are_flagged(api, voices):
    api.client.put('/settings/voices.favorites', json={'value': ['luis']}, headers=api.headers)

    assert _card(api, 'luis')['favorite'] is True
    assert _card(api, 'ana')['favorite'] is False


def test_ac7_a_built_style_gives_the_path_the_files_route_serves_and_a_missing_one_gives_none(api, voices):
    expert = next(item for item in _card(api, 'luis')['styles'] if item['style'] == 'expert')

    assert expert['path'] == 'voices/luis/expert.wav'
    assert all(item['path'] is None for item in _card(api, 'ana')['styles'])
