"""Construye voces del catálogo en la cola (spec 010, D-5 y AC-7): corre `voices.main` en el venv de CosyVoice."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.narration.voices import catalog as voice_catalog

RESOURCE = 'gpu'  # CosyVoice y whisper usan la GPU: un build a la vez, con el candado


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}: hace falta al menos una voz, y cada una tiene que estar en el catálogo."""
    voices = params.get('voices') or []
    if not voices:
        return [{'code': 'no_voices', 'params': {}}]
    known = voice_catalog.catalog()
    return [{'code': 'unknown_voice', 'params': {'voice': name}} for name in voices if name not in known]


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `voices.main --build`. `output_dir` no hace falta: cada voz escribe en su carpeta del catálogo."""
    args = ['--build', *params['voices']]
    if params.get('force'):
        args.append('--force')
    return [sys.executable, '-m', 'content_studio.narration.voices.main', *args]
