"""Sugerir palabras clave (spec 021, D-4): una por cue, con un emoji opcional, para el estilo de redes de la 014.

El índice debe existir en el cue y el emoji ser un solo grafema. Al aceptarlas, la palabra lleva `keyword`, que el ASS
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
                    'emoji': {'type': 'string', 'maxLength': 16},
                },
                'required': ['id', 'keyword_index'],
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


def checker(word_counts: dict[int, int]) -> Callable[[dict], list[str]]:
    """El índice existe en su cue y el emoji, si viene, es uno solo."""

    def check(answer: dict) -> list[str]:
        found = []
        for item in answer['cues']:
            if not 0 <= item['keyword_index'] < word_counts.get(item['id'], 0):
                found.append(f'$.cues: cue {item["id"]} has no word {item["keyword_index"]}')
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
        counts = {cue['id']: len(cue['words']) for cue in batch}
        answer = ask(cues.message('subtitles_keywords', items), SCHEMA, check=checker(counts))
        for item in answer['cues']:
            word = by_id[item['id']]['words'][item['keyword_index']]['text']
            index, emoji = item['keyword_index'], item.get('emoji') or None
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
