"""La onda del origen para elegir el tramo de importar (spec 010, D-4): duración y picos, con su propio gate."""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf


@pytest.fixture
def tone(api):
    """Un WAV de 4 s con un tono de 440 Hz."""
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
