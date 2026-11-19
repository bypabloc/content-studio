"""Textos de error de la API, en español, desde messages/es.json (spec 004, D-5)."""

from __future__ import annotations

import json
from pathlib import Path

_TEXTS: dict[str, str] = json.loads((Path(__file__).parent / 'messages' / 'es.json').read_text(encoding='utf-8'))


def t(code: str, **params: object) -> str:
    """Texto del código con sus parámetros; si falta alguno, deja la plantilla tal cual."""
    template = _TEXTS.get(code, code)
    try:
        return template.format(**params)
    except KeyError:
        return template
