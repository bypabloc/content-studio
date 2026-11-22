"""Formatos de audio y video que aceptan el limpiador y la biblioteca (spec 013, D-6). Solo stdlib."""

from __future__ import annotations

from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = frozenset({'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'})
VIDEO_EXTENSIONS = frozenset({'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v'})

# Los formatos de salida son datos (spec 015, D-1): extensión, códec y, en video, si usa NVENC cuando hay NVIDIA.
TARGETS: dict[str, dict[str, Any]] = {
    'mp3': {'kind': 'audio', 'ext': '.mp3', 'codec': 'libmp3lame'},
    'wav': {'kind': 'audio', 'ext': '.wav', 'codec': 'pcm_s16le'},
    'flac': {'kind': 'audio', 'ext': '.flac', 'codec': 'flac'},
    'ogg-opus': {'kind': 'audio', 'ext': '.ogg', 'codec': 'libopus'},
    'ogg-vorbis': {'kind': 'audio', 'ext': '.ogg', 'codec': 'libvorbis'},
    'm4a': {'kind': 'audio', 'ext': '.m4a', 'codec': 'aac'},
    'mp4-h264': {'kind': 'video', 'ext': '.mp4', 'codec': 'libx264', 'nvenc': 'h264_nvenc'},
    'mp4-h265': {'kind': 'video', 'ext': '.mp4', 'codec': 'libx265', 'nvenc': 'hevc_nvenc'},
    'webm-vp9': {'kind': 'video', 'ext': '.webm', 'codec': 'libvpx-vp9'},
    'webm-av1': {'kind': 'video', 'ext': '.webm', 'codec': 'libsvtav1'},
    'mov': {'kind': 'video', 'ext': '.mov', 'codec': 'libx264', 'nvenc': 'h264_nvenc'},
    'mkv': {'kind': 'video', 'ext': '.mkv', 'codec': 'libx264', 'nvenc': 'h264_nvenc'},
}


def is_audio(path: Path) -> bool:
    """¿Es un archivo de audio? (la extensión, sin distinguir mayúsculas)."""
    return path.suffix.lower() in AUDIO_EXTENSIONS


def is_video(path: Path) -> bool:
    """¿Es un archivo de video?"""
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_supported(path: Path) -> bool:
    """¿Es un medio que el limpiador puede abrir (audio o video)?"""
    return is_audio(path) or is_video(path)
