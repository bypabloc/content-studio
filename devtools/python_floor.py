"""Piso de sintaxis de los motores (spec 025, D-2): el mínimo de los pasos `python` de sus recetas."""

from __future__ import annotations

import json
from pathlib import Path

RECIPES = Path(__file__).resolve().parents[1] / 'server/src/content_studio/engines/recipes'


def _parse(version: str) -> tuple[int, int]:
    major, minor = version.split('.')[:2]
    return int(major), int(minor)


def engine_floor(recipes: Path = RECIPES) -> tuple[int, int]:
    """Versión mínima de Python de las recetas de motores (el código de use_venv no puede usar nada más nuevo)."""
    return min(
        _parse(step['version'])
        for path in sorted(recipes.glob('*.json'))
        for step in json.loads(path.read_text(encoding='utf-8'))['steps']
        if step['kind'] == 'python'
    )
