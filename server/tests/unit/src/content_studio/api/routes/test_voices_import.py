"""Importar un tramo de un audio o un video (spec 010, D-4 y AC-6): con permiso del dueño y ffmpeg real."""

from __future__ import annotations

import json
import subprocess

import numpy as np
import pytest
import soundfile as sf

from content_studio import paths


@pytest.fixture
def refs(api, monkeypatch):
    """Carpeta de referencias vacía para la API."""
    root = api.tmp / 'reference'
    root.mkdir()
    monkeypatch.setattr(paths, 'REFERENCE', root)
    return root


@pytest.fixture
def video(api):
    """Un video de 15 s con un tono, generado con ffmpeg."""
    path = api.tmp / 'clip.mp4'
    subprocess.run(
        [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-f', 'lavfi', '-i', 'testsrc=duration=15:size=160x120:rate=10',
            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=15',
            '-c:v', 'mpeg4', '-c:a', 'aac', str(path),
        ],
        check=True,
    )  # fmt: skip
    return path


def _create(api):
    api.client.post('/voices/profiles', json={'name': 'Spec 010'}, headers=api.headers)


def _import(api, source, **changes):
    body = {'path': str(source), 'start': 2.0, 'end': 12.0, 'style': 'expert', 'consent': True, **changes}
    return api.client.post('/voices/profiles/spec-010/import', json=body, headers=api.headers)


def test_ac6_an_import_without_consent_is_422_consent_required(api, refs, video):
    _create(api)

    response = _import(api, video, consent=False)

    assert response.status_code == 422 and response.json()['code'] == 'consent_required'


def test_ac6_a_10_second_span_of_a_video_becomes_a_take_and_the_consent_is_recorded(api, refs, video):
    _create(api)

    response = _import(api, video)

    assert response.status_code == 201 and response.json()['take'] == 1
    info = sf.info(refs / 'spec-010/takes/expert/1.wav')
    assert abs(info.duration - 10.0) <= 0.05
    assert info.samplerate == 48000 and info.channels == 1 and info.subtype == 'PCM_24'
    profile = json.loads((refs / 'spec-010/profile.json').read_text(encoding='utf-8'))
    assert profile['consent']['accepted_at'] and profile['consent']['text']


def test_a_span_must_be_between_8_and_12_seconds(api, refs, video):
    _create(api)

    response = _import(api, video, start=0.0, end=5.0)

    assert response.status_code == 422 and response.json()['code'] == 'invalid_span'


def test_a_file_that_is_not_audio_or_video_is_unreadable_media(api, refs, tmp_path):
    _create(api)
    broken = tmp_path / 'notmedia.mp4'
    broken.write_bytes(b'esto no es un video')

    response = _import(api, broken)

    assert response.status_code == 422 and response.json()['code'] == 'unreadable_media'


@pytest.fixture
def tone(api):
    """Un WAV de 4 s con un tono de 440 Hz, para la onda del origen."""
    path = api.tmp / 'tono.wav'
    t = np.arange(int(4 * 48000)) / 48000
    sf.write(path, 0.5 * np.sin(2 * np.pi * 440 * t), 48000, subtype='PCM_16')
    return path


def _peaks(api, path, **params):
    return api.client.get('/voices/import/peaks', params={'path': str(path), **params}, headers=api.headers)


def test_d4_the_peaks_give_the_duration_and_n_values_between_0_and_1(api, tone):
    response = _peaks(api, tone, n=200)

    assert response.status_code == 200
    body = response.json()
    assert abs(body['duration'] - 4.0) <= 0.05
    assert len(body['peaks']) == 200
    assert all(0 <= value <= 1 for value in body['peaks'])
    assert max(body['peaks']) > 0.3  # el tono se oye: la onda no es plana


def test_d4_a_file_that_is_not_media_is_422_unreadable_media(api):
    notes = api.tmp / 'notas.txt'
    notes.write_text('hola', encoding='utf-8')

    response = _peaks(api, notes)

    assert response.status_code == 422 and response.json()['code'] == 'unreadable_media'


def test_d4_a_missing_file_is_422_unreadable_media(api):
    response = _peaks(api, api.tmp / 'no-existe.wav')

    assert response.status_code == 422 and response.json()['code'] == 'unreadable_media'


def test_d4_a_media_file_that_ffmpeg_cannot_read_is_422_unreadable_media(api):
    broken = api.tmp / 'roto.wav'
    broken.write_bytes(b'esto no es audio')

    response = _peaks(api, broken)

    assert response.status_code == 422 and response.json()['code'] == 'unreadable_media'
