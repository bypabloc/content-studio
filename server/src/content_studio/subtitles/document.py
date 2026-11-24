"""Documento de subtítulos (spec 014, D-1): JSON en disco con cues y palabras, y operaciones puras sobre él.

Las operaciones devuelven un documento nuevo y no tocan el de entrada. Solo `load` y `save` escriben o leen disco.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

VERSION = 1


def new_document(*, source_path: str, kind: str, language: str, cues: list[dict]) -> dict[str, Any]:
    """Documento nuevo con su versión, el origen (ruta y tipo), el idioma y los cues; estilo y pistas vacíos."""
    return {
        'version': VERSION,
        'source': {'path': source_path, 'kind': kind},
        'language': language,
        'cues': cues,
        'style': {},
        'tracks': {},
    }


def _cue_from_words(cue_id: int, words: list[dict]) -> dict[str, Any]:
    return {
        'id': cue_id,
        'start': words[0]['start'],
        'end': words[-1]['end'],
        'text': ' '.join(word['text'] for word in words),
        'words': [dict(word) for word in words],
    }


def _index(doc: dict[str, Any], cue_id: int) -> int:
    for index, cue in enumerate(doc['cues']):
        if cue['id'] == cue_id:
            return index
    raise KeyError(cue_id)


def _with_cues(doc: dict[str, Any], cues: list[dict]) -> dict[str, Any]:
    result = copy.deepcopy(doc)
    result['cues'] = cues
    return result


def split(doc: dict[str, Any], cue_id: int, at_word: int) -> dict[str, Any]:
    """Parte el cue antes de la palabra `at_word`; la segunda mitad toma el id nuevo más alto."""
    cues = copy.deepcopy(doc['cues'])
    index = _index(doc, cue_id)
    words = cues[index]['words']
    if not 0 < at_word < len(words):
        raise ValueError(f'at_word {at_word} is out of range for cue {cue_id}')
    new_id = max(cue['id'] for cue in cues) + 1
    cues[index : index + 1] = [
        _cue_from_words(cue_id, words[:at_word]),
        _cue_from_words(new_id, words[at_word:]),
    ]
    return _with_cues(doc, cues)


def merge(doc: dict[str, Any], first_id: int, second_id: int) -> dict[str, Any]:
    """Une dos cues contiguos en el primero, que conserva su id."""
    cues = copy.deepcopy(doc['cues'])
    first = _index(doc, first_id)
    if _index(doc, second_id) != first + 1:
        raise ValueError(f'cues {first_id} and {second_id} are not adjacent')
    words = cues[first]['words'] + cues[first + 1]['words']
    cues[first : first + 2] = [_cue_from_words(first_id, words)]
    return _with_cues(doc, cues)


def shift(doc: dict[str, Any], cue_id: int, delta: float) -> dict[str, Any]:
    """Mueve el cue y sus palabras el mismo `delta` de segundos."""
    cues = copy.deepcopy(doc['cues'])
    cue = cues[_index(doc, cue_id)]
    cue['start'] = round(cue['start'] + delta, 6)
    cue['end'] = round(cue['end'] + delta, 6)
    for word in cue['words']:
        word['start'] = round(word['start'] + delta, 6)
        word['end'] = round(word['end'] + delta, 6)
    return _with_cues(doc, cues)


def set_text(doc: dict[str, Any], cue_id: int, text: str) -> dict[str, Any]:
    """Cambia el texto del cue. Con la misma cantidad de palabras, cada una conserva su tiempo; si cambia la cantidad,
    el intervalo del cue se reparte entre las palabras en proporción a sus caracteres. Nunca se mueve el fin del cue,
    así que no pisa al siguiente."""
    cues = copy.deepcopy(doc['cues'])
    cue = cues[_index(doc, cue_id)]
    new_words = text.split()
    if not new_words:
        raise ValueError('cue text cannot be empty')
    old_words = cue['words']
    if len(new_words) == len(old_words):
        words = [dict(old, text=new) for old, new in zip(old_words, new_words, strict=True)]
    else:
        total = sum(len(word) for word in new_words)
        span = cue['end'] - cue['start']
        words = []
        seen = 0
        for word in new_words:
            start = cue['start'] + span * seen / total
            seen += len(word)
            end = cue['start'] + span * seen / total
            words.append({'start': round(start, 6), 'end': round(end, 6), 'text': word})
        words[-1]['end'] = cue['end']
    cue['words'] = words
    cue['text'] = ' '.join(new_words)
    return _with_cues(doc, cues)


def save(doc: dict[str, Any], path: Path) -> None:
    """Guarda el documento como JSON en UTF-8, creando su carpeta si hace falta."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')


def load(path: Path) -> dict[str, Any]:
    """Lee el documento de un JSON en UTF-8."""
    return json.loads(path.read_text(encoding='utf-8'))
