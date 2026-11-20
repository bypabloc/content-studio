"""Linter del guion (spec 006, D-1): las reglas de formato-guion.md que se comprueban sin modelo.

`lint` devuelve las incidencias con línea, columna y largo; `estimate_seconds` calcula la duración aproximada.
Las marcas de la gramática (`[pausa N]`, `[estilo: x]`, `[risa]`…) se enmascaran con espacios del mismo largo, así
que las posiciones son las del texto original. Las reglas que piden criterio o un modelo no se comprueban aquí.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from content_studio.narration.styles import STYLES as STYLE_SETTINGS
from content_studio.narration.text.segments import ALIAS_KEYS, MARK, MARK_BLOCK, PAUSE_PARAGRAPH, normalize

GUIDE = 'formato-guion.md#reglas-obligatorias'
MAX_WORDS = 25
WORDS_PER_SECOND = 2.6
# Marcas de la gramática: el modelo no las lee en voz alta (regla 1).
GRAMMAR = frozenset({'pause', 'style', 'emotion', 'emphasis', 'laugh', 'sigh', 'breathing'})
# Siglas que se escriben en mayúsculas sin ser énfasis (regla 2). Cualquier otra palabra de 3 letras o más cuenta.
ACRONYMS = frozenset({'PDF', 'DNI', 'IVA', 'CEO', 'ONG', 'SMS', 'URL', 'GPS', 'USB', 'API', 'HTML', 'ONU'})
# Regla 1: etiquetas [..], <..>, ** y (pausa), más la notación de grabación (/ ↗ ↘ →).
TAG = re.compile(r'\[[^\]\n]*\]|<[^>\n]*>|\*\*|\((?:pausa|pause)\)|[/↗↘→]', re.IGNORECASE)
WORD = re.compile(r'\w{3,}')  # regla 2: palabras de 3 o más letras
NUMBER = re.compile(r'\d+(?:[.,:]\d+)*')  # regla 13
REGISTRAS = re.compile(r'(?<!\w)registras(?!\w)', re.IGNORECASE)  # regla 19
# Un párrafo es lo que hay entre líneas en blanco; una oración termina en signo, en salto de línea o al final.
PARAGRAPH = re.compile(r'(?:(?!\n[ \t]*\n)[\s\S])+')
SENTENCE = re.compile(r'[^\n]+?(?:[.?!…]+(?=\s|$)|(?=\n)|$)')

# Regla, código, índice, largo y parámetros del texto de la regla.
Found = tuple[int, str, int, int, dict[str, Any]]


@dataclass(frozen=True)
class Issue:
    """Una incidencia del linter: la regla de formato-guion.md, su código y la posición (1-based)."""

    rule: int
    code: str
    line: int
    col: int
    length: int
    params: dict[str, Any] = field(default_factory=dict)


def _grammar(m: re.Match[str]) -> str:
    """Pone en blanco una marca de la gramática; deja intacta cualquier otra."""
    key = m.group(2).lower()
    return ' ' * len(m.group(0)) if ALIAS_KEYS.get(key, key) in GRAMMAR else m.group(0)


def _masked(text: str) -> str:
    """El texto con las marcas de la gramática en blanco: las posiciones siguen siendo las del original."""
    return MARK.sub(_grammar, text)


def _visible(text: str) -> str:
    """Lo que el modelo leería: sin marcas de la gramática ni etiquetas."""
    return TAG.sub(lambda m: ' ' * len(m.group(0)), _masked(text))


def _at(text: str, index: int, length: int) -> tuple[int, int, int]:
    """Línea y columna (1-based) del índice, y el largo."""
    return text.count('\n', 0, index) + 1, index - text.rfind('\n', 0, index), length


def _labels(masked: str) -> Iterator[Found]:
    """Regla 1: etiquetas y notación de grabación."""
    for m in TAG.finditer(masked):
        yield 1, 'label', m.start(), len(m.group(0)), {'text': m.group(0)}


def _shouting(visible: str) -> Iterator[Found]:
    """Regla 2: palabras en mayúsculas que no son siglas."""
    for m in WORD.finditer(visible):
        if m.group(0).isupper() and m.group(0) not in ACRONYMS:
            yield 2, 'shout', m.start(), len(m.group(0)), {'text': m.group(0)}


def _paragraph_ends(visible: str) -> Iterator[Found]:
    """Regla 3: cada párrafo termina en punto, pregunta o exclamación (las comillas de cierre no cuentan)."""
    for m in PARAGRAPH.finditer(visible):
        body = m.group(0).rstrip()
        core = body.rstrip('»”"')
        if core.strip() and core[-1] not in '.?!':
            yield 3, 'no_end', m.start() + len(body) - 1, 1, {}


def _colons_and_semicolons(visible: str) -> Iterator[Found]:
    """Regla 6: nada de `;`, y `:` solo antes de una enumeración (una coma antes del cierre de la oración)."""
    for m in re.finditer(r'[;:]', visible):
        listed = m.group(0) == ':' and re.match(r'[^.?!\n]*,', visible[m.end() :])
        if not listed:
            code = 'semicolon' if m.group(0) == ';' else 'colon'
            yield 6, code, m.start(), 1, {'text': m.group(0)}


def _questions_and_exclamations(visible: str) -> Iterator[Found]:
    """Regla 10: toda pregunta lleva ¿ y ?, y toda exclamación ¡ y !."""
    for opening, closing in (('¿', '?'), ('¡', '!')):
        pending: list[int] = []
        for index, char in enumerate(visible):
            if char == opening:
                pending.append(index)
            elif char == closing:
                if pending:
                    pending.pop()
                else:
                    yield 10, 'missing_opening', index, 1, {'sign': opening}
        for index in pending:
            yield 10, 'missing_closing', index, 1, {'sign': closing}


def _long_sentences(visible: str) -> Iterator[Found]:
    """Regla 11: ninguna oración pasa de MAX_WORDS palabras."""
    for m in SENTENCE.finditer(visible):
        sentence = m.group(0)
        count = len(re.findall(r'\w+', sentence))
        if count > MAX_WORDS:
            start = m.start() + len(sentence) - len(sentence.lstrip())
            yield 11, 'long_sentence', start, len(sentence.strip()), {'count': count, 'max': MAX_WORDS}


def _numbers(visible: str) -> Iterator[Found]:
    """Regla 13: cifras, que van en letras."""
    for m in NUMBER.finditer(visible):
        yield 13, 'digits', m.start(), len(m.group(0)), {'text': m.group(0)}


def _registras(visible: str) -> Iterator[Found]:
    """Regla 19: «registras» se deforma en la voz."""
    for m in REGISTRAS.finditer(visible):
        yield 19, 'registras', m.start(), len(m.group(0)), {'text': m.group(0)}


def lint(text: str) -> list[Issue]:
    """Incidencias de las reglas comprobables, en orden de lectura.

    >>> [(i.rule, i.line, i.col, i.length) for i in lint('Hola; esto es DEMO con 24 horas.')]
    [(6, 1, 5, 1), (2, 1, 15, 4), (13, 1, 24, 2)]
    >>> lint('Hola [pausa 1] mundo.')
    []
    >>> [(i.rule, i.line, i.col) for i in lint('Uno.\\n\\nDos')]
    [(3, 3, 3)]
    """
    masked, visible = _masked(text), _visible(text)
    found = [
        *_labels(masked),
        *_shouting(visible),
        *_paragraph_ends(visible),
        *_colons_and_semicolons(visible),
        *_questions_and_exclamations(visible),
        *_long_sentences(visible),
        *_numbers(visible),
        *_registras(visible),
    ]
    found.sort(key=lambda f: f[2])
    return [Issue(rule, code, *_at(text, index, length), params) for rule, code, index, length, params in found]


def words(text: str) -> int:
    """Palabras que el modelo diría: sin marcas ni etiquetas.

    >>> words('Hola [pausa 1] mundo, ¿qué tal?')
    4
    """
    return len(re.findall(r'\w+', _visible(text)))


def estimate_seconds(text: str, style: str = 'expert') -> float:
    """Segundos aproximados: palabras a 2,6 por segundo por la velocidad del estilo, más las pausas del guion.

    >>> estimate_seconds(' '.join(['palabra'] * 26))
    10.0
    >>> estimate_seconds(' '.join(['palabra'] * 26), 'friendly')
    10.5
    >>> estimate_seconds('Uno. [pausa 1,5] Dos.')
    2.3
    >>> estimate_seconds('Uno.\\n\\nDos.')
    1.4
    """
    marks = list(MARK_BLOCK.finditer(normalize(text)))
    pauses = sum(float(m[1].replace(',', '.')) for m in marks if m[1])
    breaks = sum(m[0].startswith('\n') for m in marks)
    speed = float(STYLE_SETTINGS.get(style, {}).get('speed', 1.0))
    return round(words(text) / WORDS_PER_SECOND * speed + pauses + breaks * PAUSE_PARAGRAPH, 1)
