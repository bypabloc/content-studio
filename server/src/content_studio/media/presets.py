"""Presets de redes (spec 015, D-2): tamaño, fps y encuadre por defecto de cada plataforma. Solo stdlib.

El ★ (recomendado) sale de la proporción de la fuente: vertical → Reels; cuadrado → cuadrado; si no, YouTube 1080.
"""

from __future__ import annotations

from typing import Any

PRESETS: dict[str, dict[str, Any]] = {
    'reels': {'width': 1080, 'height': 1920, 'fps': 30, 'reframe': 'center', 'lufs': -14},
    'tiktok': {'width': 1080, 'height': 1920, 'fps': 30, 'reframe': 'center', 'lufs': -14},
    'shorts': {'width': 1080, 'height': 1920, 'fps': 60, 'reframe': 'center', 'lufs': -14},
    'youtube-1080': {'width': 1920, 'height': 1080, 'fps': 30, 'reframe': 'center'},
    'youtube-4k': {'width': 3840, 'height': 2160, 'fps': 30, 'reframe': 'center'},
    'square': {'width': 1080, 'height': 1080, 'fps': 30, 'reframe': 'center'},
    'x-landscape': {'width': 1280, 'height': 720, 'fps': 30, 'reframe': 'center'},
}


def recommended(aspect: float) -> str:
    """El preset ★ para una fuente de esta proporción (ancho sobre alto)."""
    if aspect < 0.8:
        return 'reels'
    if aspect < 1.25:
        return 'square'
    return 'youtube-1080'
