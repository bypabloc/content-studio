"""Envolvente de ducking (spec 016, D-1): de las palabras a los tramos de voz y a la curva de ganancia. Solo stdlib."""

from __future__ import annotations


def speech_regions(
    words: list[tuple[float, float]], merge_gap: float = 0.6, pre: float = 0.2, post: float = 0.4
) -> list[tuple[float, float]]:
    """Los tramos de voz: une las palabras separadas por menos de `merge_gap` y agrega `pre` antes y `post` después.

    >>> speech_regions([(1.0, 1.4), (1.6, 2.0), (4.0, 4.5)])
    [(0.8, 2.4), (3.8, 4.9)]
    """
    merged: list[list[float]] = []
    for start, end in sorted(words):
        if merged and start - merged[-1][1] < merge_gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(round(max(0.0, start - pre), 3), round(end + post, 3)) for start, end in merged]


def gain_curve(
    regions: list[tuple[float, float]],
    duration: float,
    duck_db: float = -12.0,
    ramp: float = 0.3,
    base_db: float = 0.0,
) -> list[tuple[float, float]]:
    """La curva de ganancia (t, dB) de 0 a `duration`: baja `ramp` s antes de cada tramo y sube `ramp` s después.

    Dos tramos cuyas rampas se solapan forman un solo valle, sin subir entre ellos.

    >>> gain_curve([(1.0, 2.0)], duration=3, ramp=0.5)
    [(0.0, 0.0), (0.5, 0.0), (1.0, -12.0), (2.0, -12.0), (2.5, 0.0), (3.0, 0.0)]
    """
    clipped = sorted(
        (max(0.0, start), min(duration, end)) for start, end in regions if min(duration, end) > max(0.0, start)
    )
    merged: list[list[float]] = []
    for start, end in clipped:
        if merged and start - ramp <= merged[-1][1] + ramp:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    points = [point for start, end in merged for point in _ramps(start, end, duck_db, ramp, base_db)]
    inside = [(t, db) for t, db in points if 0 < t < duration]
    curve = [(0.0, _value(points, 0.0, base_db)), *inside, (duration, _value(points, duration, base_db))]
    return [(round(float(t), 3), round(float(db), 3)) for t, db in curve]


def _ramps(start: float, end: float, duck_db: float, ramp: float, base_db: float) -> list[tuple[float, float]]:
    """Los cuatro puntos de un tramo: sube a `base_db` antes de `start` y vuelve a él después de `end`."""
    return [(start - ramp, base_db), (start, duck_db), (end, duck_db), (end + ramp, base_db)]


def _value(points: list[tuple[float, float]], t: float, default: float) -> float:
    """El valor de la curva en `t`: interpolado entre sus puntos y sostenido en los extremos."""
    if not points:
        return default
    if t <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:], strict=False):
        if t <= t1:
            return v0 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return points[-1][1]
