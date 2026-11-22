"""Segmentación de subtítulos (spec 014, D-2): función pura que corta palabras con tiempos en cues.

Corta primero en la puntuación fuerte (. ? !), después en la débil (, ; :) y después en el límite de caracteres o de
duración. Con `words_per_cue`, agrupa por cantidad sin cruzar la puntuación fuerte. Solo stdlib.
"""

from __future__ import annotations

from collections.abc import Sequence

STRONG = '.?!…'
WEAK = ',;:'


def wrap_lines(words: Sequence[str], max_chars: int) -> list[str]:
    """Parte las palabras en renglones de hasta `max_chars` caracteres, sin cortar ninguna palabra.

    >>> wrap_lines(['uno', 'dos', 'tres', 'cuatro'], 8)
    ['uno dos', 'tres', 'cuatro']
    """
    lines: list[str] = []
    line = ''
    for word in words:
        candidate = f'{line} {word}' if line else word
        if len(candidate) <= max_chars or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _sentences(words: Sequence[dict]) -> list[list[dict]]:
    """Trozos que terminan en puntuación fuerte, o en la última palabra."""
    sentences: list[list[dict]] = []
    current: list[dict] = []
    for word in words:
        current.append(word)
        if word['word'][-1] in STRONG:
            sentences.append(current)
            current = []
    if current:
        sentences.append(current)
    return sentences


def _fits(words: Sequence[dict], max_chars: int, max_lines: int, max_duration: float) -> bool:
    lines = wrap_lines([w['word'] for w in words], max_chars)
    return len(lines) <= max_lines and words[-1]['end'] - words[0]['start'] <= max_duration + 1e-9


def _weak_cut(words: Sequence[dict]) -> int | None:
    """Índice después de la última palabra con puntuación débil que deja algo a su derecha."""
    for index in range(len(words) - 2, -1, -1):
        if words[index]['word'][-1] in WEAK:
            return index + 1
    return None


def _cue(words: Sequence[dict]) -> dict:
    return {
        'start': words[0]['start'],
        'end': words[-1]['end'],
        'text': ' '.join(w['word'] for w in words),
        'words': list(words),
    }


def _pack(words: Sequence[dict], max_chars: int, max_lines: int, max_duration: float) -> list[list[dict]]:
    """Agrupa las palabras de una frase sin pasar los límites; si no caben, corta en puntuación débil."""
    cues: list[list[dict]] = []
    current: list[dict] = []
    queue = list(words)
    while queue:
        word = queue.pop(0)
        if current and not _fits(current + [word], max_chars, max_lines, max_duration):
            cut = _weak_cut(current)
            if cut is None:
                cues.append(current)
                current = []
                queue.insert(0, word)
            else:
                cues.append(current[:cut])
                queue[:0] = current[cut:] + [word]
                current = []
        else:
            current.append(word)
    if current:
        cues.append(current)
    return cues


def segment(
    words: Sequence[dict],
    *,
    max_chars: int = 42,
    max_lines: int = 2,
    max_duration: float = 7.0,
    words_per_cue: int | None = None,
) -> list[dict]:
    """Cues con `start`, `end`, `text` y sus `words` (las mismas palabras de entrada).

    >>> words = [{'word': 'Hola,', 'start': 0.0, 'end': 0.4}, {'word': 'mundo.', 'start': 0.5, 'end': 0.9}]
    >>> [cue['text'] for cue in segment(words)]
    ['Hola, mundo.']
    """
    if words_per_cue is not None:
        return [
            _cue(sentence[start : start + words_per_cue])
            for sentence in _sentences(words)
            for start in range(0, len(sentence), words_per_cue)
        ]
    return [_cue(cue) for sentence in _sentences(words) for cue in _pack(sentence, max_chars, max_lines, max_duration)]
