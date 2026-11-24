"""Miniaturas (spec 020, D-1): un cuadro al 10 % en una caché de disco por ruta y fecha; la base no guarda imágenes."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.library import thumbs

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


@pytest.fixture
def home(tmp_path, monkeypatch) -> Path:
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(tmp_path / 'home'))
    return tmp_path / 'home'


def test_the_cache_name_is_the_sha1_of_path_and_mtime(home):
    """`cache/thumbs/<sha1(path+mtime)>.jpg` dentro de la carpeta de datos del usuario."""
    expected = hashlib.sha1(b'D:/v.mp4|12.5').hexdigest()

    assert thumbs.thumb_path('D:/v.mp4', 12.5) == home / 'cache' / 'thumbs' / f'{expected}.jpg'


@needs_ffmpeg
def test_a_video_thumbnail_is_made_once_and_reused(home, tmp_path):
    """El primer pedido genera el JPEG; el segundo devuelve el mismo archivo sin volver a llamar a ffmpeg."""
    video = tmp_path / 'clip.mp4'
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc=size=320x240:rate=10:duration=2',
         str(video)],
        check=True,
    )  # fmt: skip
    item = {'path': str(video), 'mtime': video.stat().st_mtime, 'duration': 2.0, 'media_type': 'video'}

    first = thumbs.thumbnail(item)
    stamp = first.stat().st_mtime_ns
    second = thumbs.thumbnail(item)

    assert first == second
    assert first.read_bytes()[:2] == b'\xff\xd8'
    assert second.stat().st_mtime_ns == stamp


def test_only_videos_and_images_have_a_thumbnail(home):
    """El audio se dibuja con sus picos en el client: aquí no tiene miniatura."""
    with pytest.raises(ValueError):
        thumbs.thumbnail({'path': 'a.wav', 'mtime': 1.0, 'duration': 1.0, 'media_type': 'audio'})


def test_an_unreadable_video_raises_without_leaving_an_empty_file(home, tmp_path):
    """Si ffmpeg no puede sacar el cuadro, no queda un JPEG vacío en la caché."""
    broken = tmp_path / 'roto.mp4'
    broken.write_text('no es video', encoding='utf-8')
    item = {'path': str(broken), 'mtime': 1.0, 'duration': 1.0, 'media_type': 'video'}

    with pytest.raises(ValueError):
        thumbs.thumbnail(item)

    assert not thumbs.thumb_path(str(broken), 1.0).exists()
