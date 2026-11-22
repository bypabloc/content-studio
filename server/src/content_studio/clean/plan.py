"""Plan de cortes del limpiador: huecos entre palabras, reasignación de tiempos (spec 013, D-3).

Funciones puras, solo stdlib. Los tiempos van en segundos.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict

MIN_CUT = 0.05  # los cortes de menos de 50 ms se descartan


class Span(TypedDict):
    """Una palabra transcrita: sus tiempos en segundos."""

    start: float
    end: float


class Cut(TypedDict):
    """Un corte de silencio; `enabled` dice si se aplica."""

    start: float
    end: float
    enabled: bool


def plan(
    words: Sequence[Span],
    duration: float,
    min_gap: float = 0.5,
    padding: float = 0.15,
    edges: bool = True,
) -> list[Cut]:
    """Devuelve los cortes activos para los huecos de más de `min_gap` entre palabras.

    Cada corte deja `padding` segundos de margen a cada lado del hueco. Con `edges`, también se cortan el
    inicio y el final si el silencio supera `min_gap`.

    >>> plan([{'start': 0.0, 'end': 0.4}, {'start': 1.2, 'end': 1.6}], duration=2.0, edges=False)
    [{'start': 0.55, 'end': 1.05, 'enabled': True}]
    >>> plan([], duration=10.0)
    []
    """
    if not words:
        return []
    spans: list[tuple[float, float]] = []
    if edges and words[0]['start'] > min_gap:
        spans.append((0.0, words[0]['start'] - padding))
    for before, after in zip(words, words[1:], strict=False):
        if round(after['start'] - before['end'], 9) > min_gap:
            spans.append((before['end'] + padding, after['start'] - padding))
    if edges and duration - words[-1]['end'] > min_gap:
        spans.append((words[-1]['end'] + padding, duration - padding))
    return [
        {'start': round(start, 6), 'end': round(end, 6), 'enabled': True}
        for start, end in spans
        if end - start >= MIN_CUT
    ]


def _active(cuts: Sequence[Cut]) -> list[Cut]:
    return sorted((c for c in cuts if c['enabled']), key=lambda c: c['start'])


def keep_segments(cuts: Sequence[Cut], duration: float) -> list[tuple[float, float]]:
    """Devuelve los tramos a conservar: el complemento de los cortes activos dentro de la duración.

    >>> keep_segments([{'start': 1.0, 'end': 2.0, 'enabled': True}], 3.0)
    [(0.0, 1.0), (2.0, 3.0)]
    """
    keep: list[tuple[float, float]] = []
    position = 0.0
    for cut in _active(cuts):
        if cut['start'] > position:
            keep.append((position, cut['start']))
        position = max(position, cut['end'])
    if position < duration:
        keep.append((position, duration))
    return keep


def remap(t: float, cuts: Sequence[Cut]) -> float:
    """Pasa un tiempo del original al limpio. Un tiempo dentro de un corte se pega al inicio de ese corte.

    >>> remap(2.5, [{'start': 1.0, 'end': 2.0, 'enabled': True}])
    1.5
    >>> remap(1.5, [{'start': 1.0, 'end': 2.0, 'enabled': True}])
    1.0
    """
    removed = 0.0
    for cut in _active(cuts):
        if t >= cut['end']:
            removed += cut['end'] - cut['start']
        elif t > cut['start']:
            return cut['start'] - removed
        else:
            break
    return t - removed
