"""GET /media/info y /media/peaks (spec 006, AC-4). Algunas pruebas usan ffmpeg falso para correr sin el binario."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.common import ffmpeg


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


def test_a_silent_file_gives_a_finite_peak_floor_and_is_not_a_500(api):
    """Un archivo en silencio tiene pico -inf en ffmpeg; la API responde el piso de -120 dBFS, no un error."""
    if shutil.which('ffmpeg') is None:
        pytest.skip('ffmpeg no está en el PATH')
    path = api.tmp / 'out' / 'silence.wav'
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=16000:cl=mono', '-t', '2', str(path)],
        check=True,
    )

    response = api.client.get('/media/info', params={'path': str(path)}, headers=api.headers)

    assert response.status_code == 200
    assert response.json()['true_peak'] == -120.0


def test_a_path_with_a_nul_byte_is_403_not_500(api):
    response = api.client.get('/media/info', params={'path': 'out/a\x00b.wav'}, headers=api.headers)

    assert response.status_code == 403


@pytest.mark.parametrize('endpoint', ['/media/info', '/media/peaks'])
def test_ac4_a_path_outside_the_allowed_folders_is_403(api, endpoint):
    secret = api.tmp / 'secret.wav'
    secret.write_bytes(b'')

    response = api.client.get(endpoint, params={'path': str(secret)}, headers=api.headers)

    assert response.status_code == 403


@pytest.fixture
def audio(api, request) -> Path:
    """Un archivo propio de cada prueba dentro de out/ (la caché de la API va por ruta). No hace falta que suene."""
    path = api.tmp / 'out' / f'{request.node.name}.wav'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'RIFF')
    return path


def test_media_info_takes_its_numbers_from_ffmpeg(api, audio, monkeypatch):
    monkeypatch.setattr(ffmpeg, 'loudness', lambda path: (-16.0, -1.5))
    monkeypatch.setattr(ffmpeg, 'probe_duration', lambda path: 2.0)

    response = api.client.get('/media/info', params={'path': str(audio)}, headers=api.headers)

    assert response.status_code == 200
    assert response.json() == {'duration': 2.0, 'lufs': -16.0, 'true_peak': -1.5}


def test_media_info_of_silence_gives_the_peak_floor(api, audio, monkeypatch):
    monkeypatch.setattr(ffmpeg, 'loudness', lambda path: (-70.0, -120.0))
    monkeypatch.setattr(ffmpeg, 'probe_duration', lambda path: 2.0)

    response = api.client.get('/media/info', params={'path': str(audio)}, headers=api.headers)

    assert response.status_code == 200
    assert response.json()['true_peak'] == -120.0


def test_media_info_without_a_loudness_summary_is_422(api, audio, monkeypatch):
    def no_summary(path):
        raise ValueError('ffmpeg printed no loudness summary')

    monkeypatch.setattr(ffmpeg, 'loudness', no_summary)

    response = api.client.get('/media/info', params={'path': str(audio)}, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'unreadable_media'


def test_media_info_when_ffmpeg_fails_is_422(api, audio, monkeypatch):
    def broken(path):
        raise subprocess.CalledProcessError(1, 'ffmpeg')

    monkeypatch.setattr(ffmpeg, 'loudness', broken)

    response = api.client.get('/media/info', params={'path': str(audio)}, headers=api.headers)

    assert response.status_code == 422


def test_media_peaks_takes_its_peaks_from_ffmpeg(api, audio, monkeypatch):
    monkeypatch.setattr(ffmpeg, 'peaks', lambda path, n: [0.5] * n)

    response = api.client.get('/media/peaks', params={'path': str(audio), 'n': 3}, headers=api.headers)

    assert response.status_code == 200
    assert response.json() == {'peaks': [0.5, 0.5, 0.5]}


def test_media_peaks_when_ffmpeg_fails_is_422(api, audio, monkeypatch):
    def broken(path, n):
        raise subprocess.CalledProcessError(1, 'ffmpeg')

    monkeypatch.setattr(ffmpeg, 'peaks', broken)

    response = api.client.get('/media/peaks', params={'path': str(audio), 'n': 3}, headers=api.headers)

    assert response.status_code == 422


@pytest.fixture
def clip(api) -> Path:
    """Un video de 3 s con cuadros de colores dentro de out/. Sin ffmpeg, la prueba se salta."""
    if shutil.which('ffmpeg') is None:
        pytest.skip('ffmpeg no está en el PATH')
    path = api.tmp / 'out' / 'frame-source.mp4'
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            'ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=25:duration=3',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path),
        ],
        check=True,
    )  # fmt: skip
    return path


def test_ac11_frame_is_a_jpeg_of_the_video_at_that_second(api, clip):
    """AC-11 (vista previa): GET /media/frame devuelve un JPEG del cuadro pedido, de la fuente."""
    response = api.client.get('/media/frame', params={'path': str(clip), 't': 1.0}, headers=api.headers)

    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/jpeg'
    assert response.content[:2] == b'\xff\xd8'


def test_frame_of_a_path_outside_the_allowed_folders_is_403(api):
    secret = api.tmp / 'secret.mp4'
    secret.write_bytes(b'')

    response = api.client.get('/media/frame', params={'path': str(secret), 't': 0}, headers=api.headers)

    assert response.status_code == 403


def test_frame_past_the_end_of_the_video_is_422(api, clip):
    """Un instante después del final no tiene cuadro: 422 con `unreadable_media`, no un JPEG vacío."""
    response = api.client.get('/media/frame', params={'path': str(clip), 't': 60}, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'unreadable_media'
