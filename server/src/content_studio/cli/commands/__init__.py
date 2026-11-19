"""REGISTRO de comandos del CLI. Agregar uno: una subclase de Comando y una línea aquí."""

from __future__ import annotations

from content_studio.cli.commands.base import Command, Option
from content_studio.cli.commands.music import Music
from content_studio.cli.commands.narration import Record, Tts, Voices

__all__ = ['GROUPS', 'REGISTRY', 'Command', 'Option', 'por_key']

REGISTRY: list[Command] = [Tts(), Record(), Voices(), Music()]  # el orden del menú
GROUPS = {'narration': 'Narration: TTS cloning a voice (server/data/narration/README.md).'}


def por_key(key: str) -> Command:
    """El comando de una clave.

    >>> por_key('narration tts').module
    'content_studio.narration.tts'
    """
    return next(c for c in REGISTRY if c.key == key)
