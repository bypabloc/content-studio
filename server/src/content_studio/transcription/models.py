"""Catálogo de modelos de faster-whisper (spec 013, D-1): repo, tamaño y VRAM aproximada. Solo stdlib."""

from __future__ import annotations

from typing import NamedTuple


class WhisperSpec(NamedTuple):
    """Un modelo de faster-whisper: su repo, su tamaño en disco y su VRAM aproximada."""

    repo: str
    size_gb: float
    vram_gb: float


RECOMMENDED = 'large-v3-turbo'
MODELS: dict[str, WhisperSpec] = {
    'small': WhisperSpec('Systran/faster-whisper-small', 0.5, 1.0),
    'medium': WhisperSpec('Systran/faster-whisper-medium', 1.5, 2.0),
    'large-v3-turbo': WhisperSpec('mobiuslabsgmbh/faster-whisper-large-v3-turbo', 1.6, 3.0),
    'large-v3': WhisperSpec('Systran/faster-whisper-large-v3', 3.1, 4.5),
}


def recommended() -> str:
    """El modelo que el selector marca con ★."""
    return RECOMMENDED


def repo(model: str) -> str:
    """El repo de Hugging Face de un modelo del catálogo."""
    return MODELS[model].repo
