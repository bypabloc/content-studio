"""Protocolo de progreso de los motores (spec 004, D-4): una línea `@@progress {json}` en stdout, sin TTY ni colores."""

from __future__ import annotations

import json

PREFIX = '@@progress '


def emit(p: float, stage: str) -> None:
    """Imprime el progreso (fracción 0–1 y etapa) y lo vacía de inmediato, para que el worker lo lea a tiempo."""
    print(PREFIX + json.dumps({'p': p, 'stage': stage}), flush=True)


def parse(line: str) -> dict | None:
    """{'p', 'stage'} si la línea es de progreso; None si no lo es o está mal formada (va al log)."""
    if not line.startswith(PREFIX):
        return None
    try:
        data = json.loads(line[len(PREFIX) :])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and 'p' in data else None


def span_fraction(span: tuple[float, float], done: int, total: int) -> float:
    """Fracción global (0–1) del trabajo cuando `done` de `total` pasos de su tramo `(inicio, fin)` están hechos.

    >>> span_fraction((0.5, 1.0), 6, 12)
    0.75
    >>> span_fraction((0.0, 1.0), 0, 0)
    0.0
    """
    low, high = span
    return round(low + (high - low) * done / max(total, 1), 4)
