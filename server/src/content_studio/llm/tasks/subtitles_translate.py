"""Traducir subtítulos (spec 021, D-4): a cualquier idioma de la lista, respetando el largo del estilo.

Lotes de 30 cues con los 5 anteriores como contexto. Lo que no entra en `max_chars × max_lines` se pide de nuevo,
solo esos cues, más corto; si sigue largo, queda marcado. Un cue idéntico al original (de más de dos palabras) queda
marcado como sin traducir. La pista se guarda en `tracks[<idioma>]` solo cuando el usuario la acepta (`apply`).
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path

from content_studio.llm.tasks import cues
from content_studio.subtitles import languages
from content_studio.subtitles.document import load

ids_check = cues.ids_check
prepare = cues.prepare
Ask = Callable[..., dict]


def validate(params: dict) -> list[dict]:
    """El proyecto existe y el idioma es de la lista."""
    errors = cues.validate_project(params)
    if params.get('language') not in languages.LANGUAGES:
        errors.append({'code': 'unknown_language', 'params': {'language': params.get('language')}})
    return errors


def _flag(original: str, text: str, limit: tuple[int, int]) -> str | None:
    if not cues.fits(text, limit):
        return 'too_long'
    if text == original and len(text.split()) > 2:
        return 'untranslated'
    return None


def run(params: dict, ask: Ask) -> dict:
    """Las traducciones por cue, con su original y su marca (`too_long`, `untranslated` o ninguna)."""
    doc = load(Path(params['doc']))
    target, limit = languages.name(params['language']), cues.limits(doc)
    common = {'language': target, 'source': languages.name(doc.get('language', 'es')), 'chars': limit[0]}
    texts: dict[int, str] = {}
    for batch, context in cues.batches(doc['cues']):
        items = [{'id': cue['id'], 'text': cue['text']} for cue in batch]
        previous = json.dumps([cue['text'] for cue in context], ensure_ascii=False)
        request = cues.message('subtitles_translate', items, context=previous, lines=limit[1], **common)
        answer = ask(request, cues.SCHEMA, check=ids_check([cue['id'] for cue in batch]))
        texts.update({item['id']: ' '.join(item['text'].split()) for item in answer['cues']})
    long = [
        {'id': cue['id'], 'text': texts[cue['id']]} for cue in doc['cues'] if not cues.fits(texts[cue['id']], limit)
    ]
    if long:
        request = cues.message('subtitles_shorten', long, lines=limit[1], **common)
        answer = ask(request, cues.SCHEMA, check=ids_check([item['id'] for item in long]))
        for item in answer['cues']:
            text = ' '.join(item['text'].split())
            if cues.fits(text, limit):
                texts[item['id']] = text
    return {
        'language': params['language'],
        'cues': [
            {
                'id': cue['id'],
                'start': cue['start'],
                'end': cue['end'],
                'text': texts[cue['id']],
                'original': cue['text'],
                'flag': _flag(cue['text'], texts[cue['id']], limit),
            }
            for cue in doc['cues']
        ],
    }


def apply(doc: dict, result: dict) -> dict:
    """El documento con la pista aceptada en `tracks[<idioma>]` (con todos los id y sus tiempos)."""
    updated = copy.deepcopy(doc)
    track = [{key: cue[key] for key in ('id', 'start', 'end', 'text')} for cue in result['cues']]
    updated['tracks'] = {**doc.get('tracks', {}), result['language']: track}
    return updated
