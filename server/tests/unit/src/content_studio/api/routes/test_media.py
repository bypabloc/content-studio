"""GET /media/info y /media/peaks (spec 006, AC-4): duración, LUFS, pico y picos de un audio de 2 s, con ffmpeg real."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def wav(api) -> Path:
    """Un .wav de 2 s dentro de out/, generado con ffmpeg. Sin ffmpeg, la prueba se salta."""
    if shutil.which('ffmpeg') is None:
        pytest.skip('ffmpeg no está en el PATH')
    path = api.tmp / 'out' / 'two_seconds.wav'
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2', '-ac', '1', str(path)],
        check=True,
    )
    return path


def test_ac4_media_info_gives_duration_loudness_and_peak(api, wav):
    response = api.client.get('/media/info', params={'path': str(wav)}, headers=api.headers)

    assert response.status_code == 200
    body = response.json()
    assert abs(body['duration'] - 2.0) <= 0.01
    assert isinstance(body['lufs'], float)
    assert isinstance(body['true_peak'], float)


def test_ac4_media_peaks_gives_exactly_n_values_between_0_and_1(api, wav):
    response = api.client.get('/media/peaks', params={'path': str(wav), 'n': 100}, headers=api.headers)

    assert response.status_code == 200
    peaks = response.json()['peaks']
    assert len(peaks) == 100
    assert all(0 <= p <= 1 for p in peaks)
    assert max(peaks) > 0


@pytest.mark.parametrize('endpoint', ['/media/info', '/media/peaks'])
def test_ac4_a_path_outside_the_allowed_folders_is_403(api, endpoint):
    secret = api.tmp / 'secret.wav'
    secret.write_bytes(b'')

    response = api.client.get(endpoint, params={'path': str(secret)}, headers=api.headers)

    assert response.status_code == 403
