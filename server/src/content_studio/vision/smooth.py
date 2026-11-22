"""Suavizado de la trayectoria de la cara (spec 015, D-3): media móvil de 1 s y límite de velocidad.
Función pura, solo stdlib.

La trayectoria es el centro de la cara en x, normalizado de 0 a 1, una muestra por cuadro muestreado. Sin cara, la
muestra es `None`: se conserva la última posición (y, antes de la primera cara, el centro).
"""

from __future__ import annotations


def smooth(
    track: list[float | None],
    fps: float,
    speed_limit: float,
    window_seconds: float = 1.0,
    center: float = 0.5,
) -> list[float]:
    """La trayectoria suavizada: la media móvil (centrada, de `window_seconds`) limitada a `speed_limit` del ancho
    por segundo. `fps` es la tasa de muestreo de la trayectoria."""
    filled: list[float] = []
    last = center
    for value in track:
        if value is not None:
            last = min(1.0, max(0.0, value))
        filled.append(last)
    half = max(1, round(window_seconds * fps)) // 2
    averaged = [
        sum(filled[max(0, i - half) : i + half + 1]) / len(filled[max(0, i - half) : i + half + 1])
        for i in range(len(filled))
    ]
    step = speed_limit / fps
    out: list[float] = []
    for target in averaged:
        if not out:
            out.append(target)
            continue
        previous = out[-1]
        out.append(previous + max(-step, min(step, target - previous)))
    return out
