"""Mapeo entre el tiempo de fuente y el tiempo de timeline para velocidad constante."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

MIN_SPEED = 0.25
MAX_SPEED = 4.0


def clip_duration(clip: Mapping[str, Any]) -> float:
    """Duración en la línea de tiempo; proyectos anteriores a v3 usan velocidad uno."""
    return (clip['src_out'] - clip['src_in']) / _speed(clip.get('speed', 1))


def source_time(clip: Mapping[str, Any], timeline_time: float) -> float:
    """Mapea un tiempo absoluto del timeline al tiempo absoluto de la fuente."""
    return clip['src_in'] + (timeline_time - clip['start']) * _speed(clip.get('speed', 1))


def atempo_filters(speed: float) -> list[str]:
    """Divide la velocidad en filtros atempo dentro del rango admitido por FFmpeg."""
    remaining = _speed(speed)
    factors: list[float] = []
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5
    while remaining > 2:
        factors.append(2)
        remaining /= 2
    if not math.isclose(remaining, 1, abs_tol=1e-12):
        factors.append(remaining)
    return [f'atempo={factor:g}' for factor in factors]


def _speed(value: Any) -> float:
    """Devuelve una velocidad finita del rango v3 y rechaza booleanos."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('invalid speed')
    if not MIN_SPEED <= value <= MAX_SPEED:
        raise ValueError('invalid speed')
    return float(value)
