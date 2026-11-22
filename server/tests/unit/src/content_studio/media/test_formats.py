"""Formatos de medios que el limpiador y la biblioteca aceptan (spec 013, D-6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_studio.media import formats


@pytest.mark.parametrize('name', ['voz.wav', 'voz.mp3', 'voz.m4a', 'voz.flac'])
def test_audio_files_are_audio_and_not_video(name):
    """WAV, MP3, M4A y FLAC son audio: no pasan por el render de video."""
    assert formats.is_audio(Path(name))
    assert not formats.is_video(Path(name))


@pytest.mark.parametrize('name', ['clip.mp4', 'clip.MOV', 'clip.mkv', 'clip.webm'])
def test_video_files_are_video(name):
    """MP4, MOV, MKV y WebM son video (la búsqueda ignora mayúsculas)."""
    assert formats.is_video(Path(name))
    assert formats.is_supported(Path(name))


def test_other_files_are_not_supported():
    """Un texto o una imagen no son medios del limpiador."""
    assert not formats.is_supported(Path('guion.txt'))
    assert not formats.is_supported(Path('foto.png'))
