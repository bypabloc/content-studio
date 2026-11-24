"""Describir la música en español (spec 021, D-4): caption en inglés para ACE-Step, tonalidad, BPM y compás.

El schema limita la tonalidad a las estables del catálogo (011), el tempo a 30–300 y el compás a 2, 3, 4 o 6; `check`
rechaza un caption con tempo, tonalidad o texto en español (el cliente reintenta una vez).
«no vocals» se agrega si falta.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from content_studio.llm import prompts
from content_studio.music import styles
from content_studio.music.styles import STYLES

KEYS = sorted({style['key'] for style in STYLES.values()})
# Lo que ACE-Step recomienda para el caption, del docstring del catálogo (no se copia).
GUIDE = (styles.__doc__ or '').split('\n\n')[1].replace('\n', ' ')
NO_VOCALS = 'no vocals'
MAX_CAPTION = 300
MAX_DESCRIPTION = 1000
SCHEMA = {
    'type': 'object',
    'properties': {
        'caption': {'type': 'string', 'minLength': 1, 'maxLength': MAX_CAPTION - len(NO_VOCALS) - 2},
        'key': {'type': 'string', 'enum': KEYS},
        'bpm': {'type': 'integer', 'minimum': 30, 'maximum': 300},
        'time_signature': {'type': 'string', 'enum': ['2', '3', '4', '6']},
    },
    'required': ['caption', 'key', 'bpm', 'time_signature'],
    'additionalProperties': False,
}
TEMPO_OR_KEY = re.compile(r'\bbpm\b|\b\d{2,3}\s*(?:beats|bpm)\b|\b[A-G][#b]?\s*(?:major|minor)\b', re.IGNORECASE)
SPANISH = re.compile(
    r'[\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00bf\u00a1]|\b(?:con|para|lluvia|suave|tranquil[oa]|música|cocina)\b',
    re.IGNORECASE,
)
Ask = Callable[..., dict]


def validate(params: dict) -> list[dict]:
    """La descripción es un texto corto no vacío."""
    text = params.get('description')
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_DESCRIPTION:
        return [{'code': 'invalid_text', 'params': {}}]
    return []


def check(answer: dict) -> list[str]:
    """Lo que el schema no ve: tempo o tonalidad dentro del caption, o texto en español."""
    found = []
    if TEMPO_OR_KEY.search(answer['caption']):
        found.append('$.caption: no tempo or key inside the caption (they go in bpm and key)')
    if SPANISH.search(answer['caption']):
        found.append('$.caption: write the caption in English')
    return found


def run(params: dict, ask: Ask) -> dict:
    """Caption, tonalidad, BPM y compás como sugerencia editable."""
    examples = '\n'.join(f'- {STYLES[name]["caption"]}' for name in ('tutorial-calm', 'lofi-rain', 'corporate'))
    message = prompts.render(
        'music_caption', guide=GUIDE, examples=examples, keys=', '.join(KEYS), description=params['description']
    )
    answer = ask([{'role': 'user', 'content': message}], SCHEMA, check=check)
    caption = answer['caption'].strip().rstrip(',')
    if not caption.lower().endswith(NO_VOCALS):
        caption = f'{caption}, {NO_VOCALS}'
    return {**answer, 'caption': caption}
