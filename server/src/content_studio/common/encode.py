"""Codificador de video compartido (spec 014, D-7): el del render del limpiador (spec 013) y el de quemar subtítulos."""

from __future__ import annotations


def video_codec(nvenc: bool) -> list[str]:
    """Codificador de video: NVENC si el equipo tiene NVIDIA; si no, libx264 con CRF 18.

    >>> video_codec(nvenc=False)
    ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
    """
    if nvenc:
        return ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '19']
    return ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
