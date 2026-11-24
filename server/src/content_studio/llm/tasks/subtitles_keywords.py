"""Sugerir palabras clave (spec 021, D-4): una por cue, con un emoji opcional, para el estilo de redes de la 014.

El modelo nombra la palabra y su posición; manda la palabra, porque los modelos cuentan mal las posiciones. El emoji
debe ser un solo grafema. Al aceptarlas, la palabra lleva `keyword`, que el ASS
resalta con el color del estilo y el emoji al lado.
"""

from __future__ import annotations

import copy
import re
import unicodedata
from collections.abc import Callable, Iterable
from pathlib import Path

from content_studio.llm.tasks import cues
from content_studio.subtitles.document import load

NON_WORD = re.compile(r'\W')
MIN_LETTERS = 4  # «la», «por» o «vas» no sirven de palabra clave si el cue tiene otra mejor
REGIONAL_PAIR = re.compile('[\U0001f1e6-\U0001f1ff]{2}')
MODIFIERS = re.compile('[\ufe0f\u20e3\U0001f3fb-\U0001f3ff]')
SCHEMA = {
    'type': 'object',
    'properties': {
        'cues': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'keyword_index': {'type': 'integer', 'minimum': 0},
                    'word': {'type': 'string', 'minLength': 1},
                    'emoji': {'type': 'string', 'maxLength': 16},
                },
                'required': ['id', 'keyword_index', 'word'],
            },
        }
    },
    'required': ['cues'],
}
prepare = cues.prepare
validate = cues.validate_project
Ask = Callable[..., dict]


def single_grapheme(text: str) -> bool:
    """¿Un solo emoji? Con tono de piel, secuencia ZWJ o bandera; dos emojis o letras no."""
    if REGIONAL_PAIR.fullmatch(text):
        return True
    parts = [MODIFIERS.sub('', part) for part in text.split('\u200d')]
    return bool(text) and all(len(part) == 1 and unicodedata.category(part) == 'So' for part in parts)


def _plain(word: str) -> str:
    return NON_WORD.sub('', word.lower())


def resolve(item: dict, words: list[str]) -> int | None:
    """La posición de la palabra que nombra el modelo: la que dio si coincide, o la primera igual; None si falta."""
    wanted = _plain(item['word'])
    index = item['keyword_index']
    if 0 <= index < len(words) and _plain(words[index]) == wanted:
        return index
    return next((position for position, word in enumerate(words) if _plain(word) == wanted), None)


def checker(words_by_id: dict[int, list[str]]) -> Callable[[dict], list[str]]:
    """La palabra está en su cue, tiene contenido (si el cue lo permite) y el emoji, si viene, es uno solo."""

    def check(answer: dict) -> list[str]:
        found = []
        for item in answer['cues']:
            words = words_by_id.get(item['id'], [])
            if resolve(item, words) is None:
                found.append(f'$.cues: cue {item["id"]} has no word {item["word"]!r}')
            elif len(_plain(item['word'])) < MIN_LETTERS and any(len(_plain(word)) >= MIN_LETTERS for word in words):
                found.append(
                    f'$.cues: cue {item["id"]} needs a content word of {MIN_LETTERS}+ letters, not {item["word"]!r}'
                )
            if 'emoji' in item and item['emoji'] and not single_grapheme(item['emoji']):
                found.append(f'$.cues: cue {item["id"]} needs a single emoji')
        return found

    return check


def run(params: dict, ask: Ask) -> dict:
    """Una sugerencia por cue: el índice de la palabra, la palabra y el emoji (o None)."""
    doc = load(Path(params['doc']))
    by_id = {cue['id']: cue for cue in doc['cues']}
    suggestions = []
    for batch, _ in cues.batches(doc['cues']):
        items = [{'id': cue['id'], 'words': [word['text'] for word in cue['words']]} for cue in batch]
        words = {item['id']: item['words'] for item in items}
        answer = ask(cues.message('subtitles_keywords', items), SCHEMA, check=checker(words))
        for item in answer['cues']:
            index = resolve(item, words[item['id']])
            if index is None:  # el check ya lo pidió de nuevo; un modelo falso puede saltárselo
                continue
            word, emoji = by_id[item['id']]['words'][index]['text'], item.get('emoji') or None
            suggestions.append({'id': item['id'], 'keyword_index': index, 'word': word, 'emoji': emoji})
    return {'cues': suggestions}


def apply(doc: dict, result: dict, accepted: Iterable[int] | None = None) -> dict:
    """Marca la palabra clave de cada cue aceptado (todos si no se elige) con su emoji."""
    chosen = None if accepted is None else set(accepted)
    updated = copy.deepcopy(doc)
    by_id = {cue['id']: cue for cue in updated['cues']}
    for item in result['cues']:
        if (chosen is None or item['id'] in chosen) and item['id'] in by_id:
            word = by_id[item['id']]['words'][item['keyword_index']]
            word['keyword'] = {'emoji': item['emoji']} if item['emoji'] else {}
    return updated
