"""Bloques de palabras seguidas del mismo hablante, con la absorción de una palabra aislada (spec 035, AC-2).

Cada cambio de hablante abre un bloque. Una palabra sola de otro hablante, entre dos bloques del mismo hablante y con
pausas menores a `absorb_gap`, pasa al hablante de sus vecinos.
"""

from __future__ import annotations

from typing import Any


def _group(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for word in words:
        speaker = word.get('speaker')
        if groups and groups[-1]['speaker'] == speaker:
            groups[-1]['words'].append(word)
        else:
            groups.append({'speaker': speaker, 'words': [word]})
    return groups


def _absorb(groups: list[dict[str, Any]], absorb_gap: float) -> list[dict[str, Any]]:
    index = 1
    while index < len(groups) - 1:
        before, current, after = groups[index - 1], groups[index], groups[index + 1]
        isolated = len(current['words']) == 1 and before['speaker'] == after['speaker'] != current['speaker']
        if isolated:
            gap_before = current['words'][0]['start'] - before['words'][-1]['end']
            gap_after = after['words'][0]['start'] - current['words'][-1]['end']
            if gap_before < absorb_gap and gap_after < absorb_gap:
                before['words'] += current['words'] + after['words']
                del groups[index : index + 2]
                continue
        index += 1
    return groups


def blocks(words: list[dict[str, Any]], absorb_gap: float = 0.3) -> list[dict[str, Any]]:
    """Bloques `{speaker, start, end, words}` de palabras con hablante, en orden."""
    groups = _absorb(_group(words), absorb_gap)
    return [
        {
            'speaker': group['speaker'],
            'start': group['words'][0]['start'],
            'end': group['words'][-1]['end'],
            'words': group['words'],
        }
        for group in groups
    ]
