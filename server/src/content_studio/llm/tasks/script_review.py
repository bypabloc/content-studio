"""Revisar el guion (spec 021, D-4): el LLM corrige lo que el linter no arregla, y el código decide qué se acepta.

Se mandan los párrafos con avisos del linter (o todos, con «revisar todo»). Un párrafo revisado se descarta si el
linter da más avisos que antes, si quedan cifras (regla 13) o si las palabras de contenido cambian más de un 30 %
(otra idea), sin contar los números que se pasaron a letras.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable

from content_studio.llm import prompts
from content_studio.narration import script_lint

MAX_CHANGE = 0.3
MAX_TEXT = 50_000
PARAGRAPH = re.compile(r'\n[ \t]*\n')
CONTENT = re.compile(r'[^\W\d_]{4,}')  # las palabras cortas (artículos, preposiciones, siglas deletreadas) no cuentan
# Números escritos en letras de cuatro letras o más: no cuentan como palabras de contenido (regla 13).
NUMBER_WORDS = frozenset(
    [
        'cero',
        'cuatro',
        'cinco',
        'seis',
        'siete',
        'ocho',
        'nueve',
        'diez',
        'once',
        'doce',
        'trece',
        'catorce',
        'quince',
        'dieciséis',
        'diecisiete',
        'dieciocho',
        'diecinueve',
        'veinte',
        'veintiuno',
        'veintiuna',
        'veintidós',
        'veintitrés',
        'veinticuatro',
        'veinticinco',
        'veintiséis',
        'veintisiete',
        'veintiocho',
        'veintinueve',
        'treinta',
        'cuarenta',
        'cincuenta',
        'sesenta',
        'setenta',
        'ochenta',
        'noventa',
        'cien',
        'ciento',
        'doscientos',
        'doscientas',
        'trescientos',
        'trescientas',
        'cuatrocientos',
        'cuatrocientas',
        'quinientos',
        'quinientas',
        'seiscientos',
        'seiscientas',
        'setecientos',
        'setecientas',
        'ochocientos',
        'ochocientas',
        'novecientos',
        'novecientas',
        'millón',
        'millones',
    ]
)
CHANGE = {
    'type': 'object',
    'properties': {'rule': {'type': 'integer'}, 'before': {'type': 'string'}, 'after': {'type': 'string'}},
    'required': ['rule', 'before', 'after'],
}
SCHEMA = {
    'type': 'object',
    'properties': {
        'paragraphs': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'index': {'type': 'integer', 'minimum': 0},
                    'revised': {'type': 'string', 'minLength': 1},
                    'changes': {'type': 'array', 'items': CHANGE},
                },
                'required': ['index', 'revised', 'changes'],
            },
        }
    },
    'required': ['paragraphs'],
}
Ask = Callable[..., dict]


def validate(params: dict) -> list[dict]:
    """El guion es un texto no vacío de tamaño razonable."""
    text = params.get('text')
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
        return [{'code': 'invalid_text', 'params': {}}]
    return []


def content_words(text: str) -> int:
    """Palabras de contenido: de cuatro letras o más y sin contar los números escritos en letras.

    >>> content_words('Tienes veinticuatro horas. Es demo.'), content_words('Tienes 24 horas; es DEMO.')
    (3, 3)
    """
    return sum(word.lower() not in NUMBER_WORDS for word in CONTENT.findall(text))


def problems(original: str, revised: str) -> list[str]:
    """Por qué se descarta un párrafo revisado; vacío si se acepta."""
    found = []
    if script_lint.NUMBER.search(script_lint._visible(revised)):
        found.append('digits remain (rule 13)')
    if len(script_lint.lint(revised)) > len(script_lint.lint(original)):
        found.append('the lint got worse')
    before, after = content_words(original), content_words(revised)
    if abs(after - before) > MAX_CHANGE * max(before, 1):
        found.append(f'content words changed from {before} to {after}')
    return found


def run(params: dict, ask: Ask) -> dict:
    """Las sugerencias aceptadas (con antes, después y avisos) y las descartadas con sus motivos."""
    paragraphs = PARAGRAPH.split(params['text'].strip())
    issues = [script_lint.lint(text) for text in paragraphs]
    targets = [i for i, found in enumerate(issues) if params.get('all') or found]
    result: dict[str, list] = {'paragraphs': [], 'discarded': []}
    if not targets:
        return result
    payload = [{'index': i, 'text': paragraphs[i], 'issues': sorted({f.code for f in issues[i]})} for i in targets]
    message = prompts.render(
        'script_review', rules=prompts.guide_rules(), paragraphs=json.dumps(payload, ensure_ascii=False, indent=1)
    )
    answer = ask([{'role': 'user', 'content': message}], SCHEMA)
    seen: set[int] = set()
    for item in answer['paragraphs']:
        index, revised = item['index'], item['revised'].strip()
        if index not in targets or index in seen or revised == paragraphs[index]:
            continue
        seen.add(index)
        reasons = problems(paragraphs[index], revised)
        if reasons:
            result['discarded'].append({'index': index, 'revised': revised, 'reasons': reasons})
            continue
        result['paragraphs'].append(
            {
                'index': index,
                'original': paragraphs[index],
                'revised': revised,
                'changes': item['changes'],
                'issues_before': len(issues[index]),
                'issues_after': len(script_lint.lint(revised)),
            }
        )
    return result
