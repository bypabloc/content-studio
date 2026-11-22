"""Formatos de audio y video que aceptan el limpiador y la biblioteca (spec 013, D-6). Solo stdlib."""

from __future__ import annotations

from pathlib import Path

AUDIO_EXTENSIONS = frozenset({'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'})
VIDEO_EXTENSIONS = frozenset({'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v'})


def is_audio(path: Path) -> bool:
    """¿Es un archivo de audio? (la extensión, sin distinguir mayúsculas)."""
    return path.suffix.lower() in AUDIO_EXTENSIONS


def is_video(path: Path) -> bool:
    """¿Es un archivo de video?"""
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_supported(path: Path) -> bool:
    """¿Es un medio que el limpiador puede abrir (audio o video)?"""
    return is_audio(path) or is_video(path)
