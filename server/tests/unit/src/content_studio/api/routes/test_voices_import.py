"""Importar un tramo de un audio o un video (spec 010, D-4 y AC-6): con permiso del dueño y ffmpeg real."""

from __future__ import annotations

import json
import subprocess

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
