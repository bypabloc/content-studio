"""REGISTRO de comandos del CLI. Agregar uno: una subclase de Comando y una línea aquí."""

from __future__ import annotations

from content_studio.cli.commands.base import Command, Option
from content_studio.cli.commands.music import Music
from content_studio.cli.commands.narration import Record, Tts, Voices

__all__ = ['GROUPS', 'REGISTRY', 'Command', 'Option', 'por_clave']

REGISTRY: list[Command] = [Tts(), Record(), Voices(), Music()]  # el orden del menú
GROUPS = {'narration': 'Narración TTS clonando una voz (server/data/narration/README.md).'}


def por_clave(clave: str) -> Command:
    """El comando de una clave.

    >>> por_clave('narration tts').module
    'content_studio.narration.tts'
    """
    return next(c for c in REGISTRY if c.clave == clave)
