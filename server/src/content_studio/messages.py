"""Textos visibles del server: el catálogo de messages/es.json (spec 004, D-5; spec 007, D-1 y D-2)."""

from __future__ import annotations

import json
from pathlib import Path

_TEXTS: dict[str, str] = json.loads((Path(__file__).parent / 'messages' / 'es.json').read_text(encoding='utf-8'))


def t(key: str, **params: object) -> str:
    """Texto de la clave con sus parámetros. Si falta un parámetro deja la plantilla; si falta la clave, la devuelve."""
    template = _TEXTS.get(key, key)
    try:
        return template.format(**params)
    except KeyError:
        return template
