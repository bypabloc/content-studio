"""Corregir la transcripción (spec 021, D-4): nombres propios y marcas con el glosario del usuario.

Cada cue corregido conserva los tiempos de sus palabras: el texto nuevo se alinea con las palabras originales
(`subtitles.sources.align`, la alineación de la 014). Un cue con más de 2 palabras de diferencia queda «para revisar» y
`apply` solo lo aplica si el usuario lo acepta.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from pathlib import Path

from content_studio.llm.tasks import cues
from content_studio.subtitles import document
from content_studio.subtitles.sources import align

MAX_WORD_CHANGE = 2
MAX_GLOSSARY = 200
prepare = cues.prepare
Ask = Callable[..., dict]


def validate(params: dict) -> list[dict]:
    """El proyecto existe y el glosario es una lista de textos cortos."""
    errors = cues.validate_project(params)
    glossary = params.get('glossary', [])
    valid = isinstance(glossary, list) and len(glossary) <= MAX_GLOSSARY
    if not valid or not all(isinstance(term, str) and 0 < len(term) <= 80 for term in glossary):
        errors.append({'code': 'invalid_glossary', 'params': {}})
    return errors


def _timed(text: str, words: list[dict]) -> list[dict] | None:
    if not words:
        return None
    heard = [{'word': word['text'], 'start': word['start'], 'end': word['end']} for word in words]
    return [{'text': word['word'], 'start': word['start'], 'end': word['end']} for word in align(text, heard)]


def run(params: dict, ask: Ask) -> dict:
    """Los cues que cambian, con el texto original, el nuevo, sus palabras con tiempo y si piden revisión."""
    doc = document.load(Path(params['doc']))
    by_id = {cue['id']: cue for cue in doc['cues']}
    glossary = '\n'.join(f'- {term}' for term in params.get('glossary', [])) or '(vacío)'
    proposals = []
    for batch, _ in cues.batches(doc['cues']):
        items = [{'id': cue['id'], 'text': cue['text']} for cue in batch]
        request = cues.message('subtitles_correct', items, glossary=glossary)
        answer = ask(request, cues.SCHEMA, check=cues.ids_check([cue['id'] for cue in batch]))
        for item in answer['cues']:
            cue, text = by_id[item['id']], ' '.join(item['text'].split())
            if text == cue['text']:
                continue
            review = abs(len(text.split()) - len(cue['text'].split())) > MAX_WORD_CHANGE
            words = None if review else _timed(text, cue['words'])
            proposals.append({'id': cue['id'], 'original': cue['text'], 'text': text, 'words': words, 'review': review})
    return {'cues': proposals}


def apply(doc: dict, result: dict, accepted: Iterable[int] | None = None) -> dict:
    """Aplica lo aceptado; sin elegir, solo lo que no pide revisión. Sin tiempos alineados, reparte el intervalo."""
    chosen = None if accepted is None else set(accepted)
    updated = copy.deepcopy(doc)
    for proposal in result['cues']:
        if (chosen is None and proposal['review']) or (chosen is not None and proposal['id'] not in chosen):
            continue
        if proposal['words']:
            cue = next(cue for cue in updated['cues'] if cue['id'] == proposal['id'])
            cue['text'], cue['words'] = proposal['text'], copy.deepcopy(proposal['words'])
        else:
            updated = document.set_text(updated, proposal['id'], proposal['text'])
    return updated
