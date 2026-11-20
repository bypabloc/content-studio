"""Perfiles de voz propia (spec 010, D-1, AC-2): crear, renombrar y borrar sin perder bytes."""

from __future__ import annotations

import json

import pytest

from content_studio import paths
from content_studio.narration import profiles


@pytest.fixture
def refs(tmp_path, monkeypatch):
    """Una carpeta de referencias vacía en lugar de server/data/narration/reference/."""
    root = tmp_path / 'reference'
    root.mkdir()
    monkeypatch.setattr(paths, 'REFERENCE', root)
    monkeypatch.setattr(paths, 'ROOT', tmp_path)  # las rutas que da la API son relativas a la raíz, como /files
    return root


def test_ac2_create_rename_and_delete_an_empty_profile(refs):
    slug = profiles.create('Spec 010')

    assert slug == 'spec-010'
    assert json.loads((refs / 'spec-010/profile.json').read_text(encoding='utf-8'))['name'] == 'Spec 010'
    profiles.rename(slug, 'Voz de prueba')
    assert profiles.list_profiles()[0]['name'] == 'Voz de prueba'
    assert (refs / 'spec-010').is_dir()  # renombrar cambia el nombre visible, no la carpeta
    profiles.delete(slug)
    assert not (refs / 'spec-010').exists()


def test_ac2_a_profile_with_takes_needs_confirm_and_moves_to_trash(refs):
    slug = profiles.create('Spec 010')
    (refs / slug / 'takes/expert').mkdir(parents=True)
    (refs / slug / 'takes/expert/1.wav').write_bytes(b'TOMA')

    with pytest.raises(profiles.ProfileNotEmpty):
        profiles.delete(slug)
    assert (refs / slug / 'takes/expert/1.wav').read_bytes() == b'TOMA'

    profiles.delete(slug, confirm=True)
    assert not (refs / slug).exists()
    moved = list((refs / '.trash').rglob('1.wav'))
    assert len(moved) == 1 and moved[0].read_bytes() == b'TOMA'


def test_create_never_overwrites_an_existing_profile(refs):
    slug = profiles.create('Spec 010')
    (refs / slug / 'expert.wav').write_bytes(b'WAV')

    with pytest.raises(profiles.ProfileExists):
        profiles.create('Spec 010')
    assert (refs / slug / 'expert.wav').read_bytes() == b'WAV'


def test_reference_for_builds_the_profile_path(refs):
    assert profiles.reference_for('default', 'expert') == refs / 'default' / 'expert.wav'
    assert profiles.reference_for('default', 'expert', '.txt') == refs / 'default' / 'expert.txt'


def test_list_profiles_offers_only_the_styles_each_one_has(refs):
    (refs / 'default').mkdir()
    (refs / 'default/expert.wav').write_bytes(b'WAV')
    (refs / 'default/clear.wav').write_bytes(b'WAV')
    (refs / 'default/clear.txt').write_text('texto', encoding='utf-8')
    (refs / 'default/profile.json').write_text(json.dumps({'name': 'Mi voz'}), encoding='utf-8')
    (refs / 'parcial').mkdir()
    (refs / 'parcial/steady.wav').write_bytes(b'WAV')

    assert profiles.list_profiles() == [
        {'id': 'default', 'name': 'Mi voz', 'styles': ['clear', 'expert']},
        {'id': 'parcial', 'name': 'parcial', 'styles': ['steady']},
    ]


def test_styles_status_says_which_styles_have_a_chosen_reference_and_how_many_takes(refs):
    slug = profiles.create('Spec 010')
    (refs / slug / 'expert.wav').write_bytes(b'WAV')
    (refs / slug / 'takes/expert').mkdir(parents=True)
    (refs / slug / 'takes/expert/1.wav').write_bytes(b'T1')
    (refs / slug / 'takes/expert/2.wav').write_bytes(b'T2')

    status = {item['style']: item for item in profiles.styles_status(slug)}

    assert status['expert'] == {
        'style': 'expert',
        'chosen': True,
        'takes': 2,
        'reference': 'reference/spec-010/expert.wav',
    }
    assert status['clear'] == {'style': 'clear', 'chosen': False, 'takes': 0, 'reference': None}


def test_a_name_that_is_not_a_slug_is_not_a_profile(refs):
    assert not profiles.exists('../reference')
    with pytest.raises(ValueError):
        profiles.reference_for('../x', 'expert')
