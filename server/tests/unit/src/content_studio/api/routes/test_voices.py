"""API de voces (spec 010, D-1, D-3 y AC-2): perfiles, tomas, elegir y el kit de grabación."""

from __future__ import annotations

import json

import pytest

from content_studio import paths

WAV = b'RIFF\x00\x00\x00\x00WAVEfmt '


@pytest.fixture
def refs(api, monkeypatch):
    """Carpeta de referencias vacía para la API."""
    root = api.tmp / 'reference'
    root.mkdir()
    monkeypatch.setattr(paths, 'REFERENCE', root)
    monkeypatch.setattr(paths, 'ROOT', api.tmp)  # las rutas que da la API son relativas a la raíz, como /files
    return root


def _create(api, name='Spec 010'):
    return api.client.post('/voices/profiles', json={'name': name}, headers=api.headers)


def test_ac2_create_rename_and_delete_a_profile(api, refs):
    created = _create(api)
    assert created.status_code == 201 and created.json()['id'] == 'spec-010'

    renamed = api.client.patch('/voices/profiles/spec-010', json={'name': 'Voz'}, headers=api.headers)
    assert renamed.status_code == 200 and renamed.json()['name'] == 'Voz'

    assert api.client.delete('/voices/profiles/spec-010', headers=api.headers).status_code == 204
    assert not (refs / 'spec-010').exists()


def test_ac2_a_profile_that_already_exists_is_409(api, refs):
    _create(api)

    again = _create(api)

    assert again.status_code == 409 and again.json()['code'] == 'profile_exists'


def test_ac2_a_profile_with_takes_needs_confirm_and_goes_to_trash(api, refs):
    _create(api)
    api.client.post('/voices/profiles/spec-010/takes/expert', content=WAV, headers=api.headers)

    blocked = api.client.delete('/voices/profiles/spec-010', headers=api.headers)

    assert blocked.status_code == 409 and blocked.json()['code'] == 'profile_not_empty'
    assert (refs / 'spec-010/takes/expert/1.wav').read_bytes() == WAV
    gone = api.client.delete('/voices/profiles/spec-010?confirm=true', headers=api.headers)
    assert gone.status_code == 204 and not (refs / 'spec-010').exists()
    assert list((refs / '.trash').rglob('1.wav'))


def test_a_take_is_saved_numbered_listed_and_chosen(api, refs):
    _create(api)

    saved = api.client.post('/voices/profiles/spec-010/takes/expert', content=WAV, headers=api.headers)
    assert saved.status_code == 201 and saved.json()['style'] == 'expert' and saved.json()['take'] == 1

    chosen = api.client.post('/voices/profiles/spec-010/takes/expert/1/choose', headers=api.headers)
    assert chosen.status_code == 200
    assert (refs / 'spec-010/expert.wav').read_bytes() == WAV
    listed = api.client.get('/voices/profiles/spec-010/takes/expert', headers=api.headers)
    assert listed.json() == {'style': 'expert', 'takes': [1]}


def test_a_saved_take_queues_its_check_as_a_voice_check_job(api, refs):
    _create(api)

    saved = api.client.post('/voices/profiles/spec-010/takes/expert', content=WAV, headers=api.headers).json()

    jobs = api.client.get('/jobs', headers=api.headers).json()
    queued = [job for job in jobs if job['id'] == saved['job']]
    assert len(queued) == 1 and queued[0]['kind'] == 'voice.check'
    assert queued[0]['params'] == {'profile': 'spec-010', 'style': 'expert', 'take': 1}


def test_the_profile_detail_shows_each_style_with_its_chosen_reference_and_takes(api, refs):
    _create(api)
    api.client.post('/voices/profiles/spec-010/takes/expert', content=WAV, headers=api.headers)
    api.client.post('/voices/profiles/spec-010/takes/expert/1/choose', headers=api.headers)

    body = api.client.get('/voices/profiles/spec-010', headers=api.headers).json()

    assert body['id'] == 'spec-010' and body['name'] == 'Spec 010'
    expert = next(item for item in body['styles'] if item['style'] == 'expert')
    assert expert == {'style': 'expert', 'chosen': True, 'takes': 1, 'reference': 'reference/spec-010/expert.wav'}


def test_a_missing_profile_or_take_is_404_and_an_unknown_style_is_422(api, refs):
    assert api.client.get('/voices/profiles/nope', headers=api.headers).status_code == 404
    _create(api)

    assert api.client.post('/voices/profiles/spec-010/takes/nope', content=WAV, headers=api.headers).status_code == 422
    missing = api.client.post('/voices/profiles/spec-010/takes/expert/9/choose', headers=api.headers)
    assert missing.status_code == 404 and missing.json()['code'] == 'take_not_found'


def test_the_kit_gives_the_styles_in_guide_order_with_duration_ppm_and_text(api):
    styles = api.client.get('/voices/kit', headers=api.headers).json()['styles']

    assert [item['style'] for item in styles][:2] == ['neutral', 'friendly']
    neutral = styles[0]
    assert neutral['duration'] == {'min': 10, 'max': 12} and neutral['ppm'] == 150
    assert neutral['text'].startswith('Hoy quiero contarte')
    assert styles[-1]['style'] == 'whisper' and styles[-1]['optional'] is True


def test_a_style_without_a_chosen_take_has_no_reference_path(api, refs):
    _create(api)

    body = api.client.get('/voices/profiles/spec-010', headers=api.headers).json()

    expert = next(item for item in body['styles'] if item['style'] == 'expert')
    assert expert['reference'] is None


def test_a_take_detail_gives_its_path_and_its_check_once_the_job_ran(api, refs):
    _create(api)
    api.client.post('/voices/profiles/spec-010/takes/expert', content=WAV, headers=api.headers)

    before = api.client.get('/voices/profiles/spec-010/takes/expert/1', headers=api.headers).json()
    assert before == {'take': 1, 'path': 'reference/spec-010/takes/expert/1.wav', 'check': None}

    check = {'verdict': 'ok', 'reasons': [], 'messages': [], 'measures': {'duration': 10.0}}
    (refs / 'spec-010' / 'takes' / 'expert' / '1.check.json').write_text(json.dumps(check), encoding='utf-8')
    after = api.client.get('/voices/profiles/spec-010/takes/expert/1', headers=api.headers).json()
    assert after['check'] == check


def test_a_missing_take_detail_is_404(api, refs):
    _create(api)

    missing = api.client.get('/voices/profiles/spec-010/takes/expert/9', headers=api.headers)
    assert missing.status_code == 404 and missing.json()['code'] == 'take_not_found'
