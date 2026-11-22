"""Codificador de video compartido (spec 014, D-7): el mismo que usa el render del limpiador (spec 013)."""

from __future__ import annotations

from content_studio.common.encode import video_codec


def test_nvenc_when_there_is_an_nvidia_gpu():
    assert video_codec(nvenc=True) == ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '19']


def test_libx264_when_there_is_no_nvidia_gpu():
    assert video_codec(nvenc=False) == ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
