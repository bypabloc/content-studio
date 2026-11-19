"""REGISTRO de comandos del CLI. Agregar uno: una subclase de Comando y una línea aquí."""

from __future__ import annotations

from content_studio.cli.comandos.base import Comando, Opcion
from content_studio.cli.comandos.music import Musica
from content_studio.cli.comandos.narration import Grabar, Tts, Voces

__all__ = ['GRUPOS', 'REGISTRO', 'Comando', 'Opcion', 'por_clave']

REGISTRO: list[Comando] = [Tts(), Grabar(), Voces(), Musica()]  # el orden del menú
GRUPOS = {'narration': 'Narración TTS clonando una voz (narration/README.md).'}


def por_clave(clave: str) -> Comando:
    """El comando de una clave.

    >>> por_clave('narration tts').modulo
    'content_studio.narration.tts'
    """
    return next(c for c in REGISTRO if c.clave == clave)
