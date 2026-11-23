"""Interpolación pura de keyframes; el espejo TypeScript usa las mismas fixtures."""

from __future__ import annotations

from typing import Any

Frame = dict[str, Any]
Segment = tuple[float, float, float, float, str]


def value_at(keyframes: list[Frame], t: float, default: float) -> float:
    """Evalúa una propiedad en el tiempo relativo del clip; sin keyframes conserva `default`."""
    if not keyframes:
        return default
    if t <= keyframes[0]['t']:
        return float(keyframes[0]['value'])
    for left, right in zip(keyframes, keyframes[1:], strict=False):
        if t >= right['t']:
            continue
        start, end = float(left['t']), float(right['t'])
        if left['ease'] == 'hold':
            return float(left['value'])
        progress = (t - start) / (end - start)
        if left['ease'] == 'ease-in-out':
            progress = 3 * progress**2 - 2 * progress**3
        return float(left['value']) + (float(right['value']) - float(left['value'])) * progress
    return float(keyframes[-1]['value'])


def segments(keyframes: list[Frame], clip_duration: float) -> list[Segment]:
    """Expande keyframes en tramos hasta el fin del clip; el valor final se mantiene."""
    if not keyframes or clip_duration <= 0:
        return []
    end = float(clip_duration)
    first = keyframes[0]
    result: list[Segment] = []
    if first['t'] > 0:
        result.append((0.0, min(float(first['t']), end), float(first['value']), float(first['value']), 'hold'))
    for left, right in zip(keyframes, keyframes[1:], strict=False):
        start, stop = float(left['t']), min(float(right['t']), end)
        if start >= end:
            break
        if stop > start:
            result.append((start, stop, float(left['value']), float(right['value']), left['ease']))
    last = keyframes[-1]
    start = max(0.0, float(last['t']))
    if start < end:
        result.append((start, end, float(last['value']), float(last['value']), 'hold'))
    if len(keyframes) == 1 and not result:
        result.append((0.0, end, float(first['value']), float(first['value']), 'hold'))
    return result
