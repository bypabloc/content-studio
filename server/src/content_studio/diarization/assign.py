"""Hablante de cada palabra con los turnos exclusivos de pyannote (spec 035, AC-1 y D-1).

Una palabra toma el hablante con más solape. Sin solape, toma el turno más cercano si está a `max_gap` segundos o menos.
Una palabra sin `end` cuenta como un instante (su `start`).
"""

from __future__ import annotations

from typing import Any

MAX_GAP = 1.0  # segundos: más lejos de todo turno, la palabra queda sin hablante


def _speaker_at(start: float, end: float, turns: list[dict[str, Any]], max_gap: float) -> str | None:
    """El hablante con más solape; si ninguno solapa, el más cercano dentro de `max_gap`."""
    best, best_overlap = None, 0.0
    for turn in turns:
        overlap = min(end, turn['end']) - max(start, turn['start'])
        if overlap > best_overlap:
            best, best_overlap = turn['speaker'], overlap
    if best is not None:
        return best
    nearest, nearest_gap = None, float('inf')
    for turn in turns:
        gap = max(0.0, turn['start'] - end, start - turn['end'])
        if gap < nearest_gap:
            nearest, nearest_gap = turn['speaker'], gap
    return nearest if nearest_gap <= max_gap else None


def assign_speakers(
    words: list[dict[str, Any]], turns: list[dict[str, Any]], max_gap: float = MAX_GAP
) -> list[dict[str, Any]]:
    """Copia cada palabra con su `speaker`; None si ningún turno está dentro de `max_gap`."""
    return [
        {
            **word,
            'speaker': _speaker_at(float(word['start']), float(word.get('end', word['start'])), turns, max_gap),
        }
        for word in words
    ]


def segment_speaker(words: list[dict[str, Any]]) -> str | None:
    """El hablante con más duración dentro del segmento; None si ninguna palabra tiene hablante.

    >>> segment_speaker([{'start': 0, 'end': 1, 'speaker': 'A'}, {'start': 1, 'end': 3, 'speaker': 'B'}])
    'B'
    """
    totals: dict[str, float] = {}
    for word in words:
        if word.get('speaker') is not None:
            seconds = float(word.get('end', word['start'])) - float(word['start'])
            totals[word['speaker']] = totals.get(word['speaker'], 0.0) + seconds
    return max(totals, key=lambda speaker: totals[speaker]) if totals else None
