"""Corte del guion en bloques: oraciones de hasta MAX_CHARS, pausas, [style:] y [emotion:] (§5.1).

Las marcas en español ([pausa], [estilo:], [emocion:], [risa], [suspiro], [respiro], [enfasis]) son alias de las
canónicas: `normalizar` las cambia antes de cortar, así que un guion con cualquiera de las dos da los mismos bloques.
Los alias viven en narration/script_aliases.json. Ver server/data/narration/docs/formato-guion.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

MAX_CHARS = 300
PAUSE_SEG = 0.25
PAUSE_PARAGRAPH = 0.6
ALIASES = json.loads((Path(__file__).resolve().parents[1] / 'script_aliases.json').read_text(encoding='utf-8'))


def _invert(pares: dict[str, list[str]]) -> dict[str, str]:
    return {alias: canonical for canonical, aliases in pares.items() for alias in aliases}


ALIAS_KEYS = {
    alias: canonical for canonical, aliases in ALIASES.items() if isinstance(aliases, list) for alias in aliases
}
ALIAS_STYLES = _invert(ALIASES['styles'])
ALIAS_EMOTIONS = _invert(ALIASES['emotions'])
MARK = re.compile(r'\[(/?)(\w+)(:\s*|\s+)?([^\]]*)\]', re.IGNORECASE)
PAREN_LABEL = re.compile(r'\((\w+)\)')
# Marcas que cortan el texto en bloques: [pause N] (grupo 1), [style: nombre] (2),
# [emotion: nombre 0.4] (3 y 4) y la línea en blanco. El modelo no las ve.
MARK_BLOCK = re.compile(
    r'\[pause\s+(\d+(?:[.,]\d+)?)\s*s?\]'
    r'|\[style:\s*([\w-]*)\s*\]'
    r'|\[emotion:\s*(\w*)\s*(\d+(?:[.,]\d+)?)?\s*\]'
    r'|\n[ \t]*\n',
    re.IGNORECASE,
)
# Todas las marcas de la gramática, para quitarlas antes de comparar o de buscar etiquetas ajenas.
NO_MARKS = re.compile(
    r'\[pause\s+[\d.,]+\s*s?\]|\[style:[^\]]*\]|\[emotion:[^\]]*\]'
    r'|\[(?:laugh|sigh|breathing)\]|\[/?emphasis\]|\n[ \t]*\n',
    re.IGNORECASE,
)
# Qwen Base lee estas marcas en voz alta ("[breath]" sonó "Braids"). Ver docs/formato-guion.md.
LABEL = re.compile(r'\[[^\]]*\]|<[^>]*>|\*\*|\(pause\)', re.IGNORECASE)


def _value(rest: str, names: dict[str, str]) -> str:
    return re.sub(r'^(\s*)([\w-]+)', lambda m: m.group(1) + names.get(m.group(2), m.group(2)), rest, count=1)


def _mark(m: re.Match) -> str:
    bar, key, sep, rest = m.groups()
    canonical = ALIAS_KEYS.get(key.lower(), key.lower())
    if canonical == 'style':
        rest = _value(rest, ALIAS_STYLES)
    elif canonical == 'emotion':
        rest = _value(rest, ALIAS_EMOTIONS)
    return f'[{bar}{canonical}{sep or ""}{rest}]'


def normalize(text: str) -> str:
    """Pasa las marcas, los paréntesis y los nombres de estilo y emoción en español a su forma canónica.

    >>> normalize('Uno. [pausa 1] [estilo: dramatica] [emocion: triste 0.4] [enfasis]sí[/enfasis] [risa]')
    'Uno. [pause 1] [style: dramatic] [emotion: sad 0.4] [emphasis]sí[/emphasis] [laugh]'
    >>> normalize('[pause 1] [style: expert] (pausa) [breath] [emotion:]')
    '[pause 1] [style: expert] (pause) [breath] [emotion:]'
    """
    text = MARK.sub(_mark, text)
    return PAREN_LABEL.sub(lambda m: f'({ALIAS_KEYS[m.group(1)]})' if m.group(1) in ALIAS_KEYS else m.group(0), text)


def chunks(text: str) -> list[str]:
    """Agrupa oraciones en bloques de hasta MAX_CHARS.

    >>> chunks('Hola. ' * 3)
    ['Hola. Hola. Hola.']
    >>> len(chunks('a' * 200 + '. ' + 'b' * 200 + '.'))
    2
    """
    out: list[str] = []
    for sentence in re.split(r'(?<=[.!?…])\s+', ' '.join(text.split())):
        if out and len(out[-1]) + len(sentence) < MAX_CHARS:
            out[-1] += ' ' + sentence
        elif sentence:
            out.append(sentence)
    return out


def segments(text: str, style: str = 'expert') -> list[dict]:
    """Bloques a generar, cada uno con su silencio final, su estilo y su emoción (§5.1).

    Una línea en blanco deja PAUSE_PARAGRAPH. [pause N] deja N segundos: si hay alguna entre dos bloques,
    mandan esas marcas (se suman) y no las líneas en blanco. [style:] y [emotion:] cortan el bloque: el
    cambio rige desde ese punto hasta el próximo de su tipo. Un corte a mitad de oración deja un aviso.

    >>> [(b['text'], b['pause']) for b in segments('Hola. Chao.')]
    [('Hola. Chao.', 0.0)]
    >>> [(b['text'], b['pause']) for b in segments('Uno.\\n\\nDos.')]
    [('Uno.', 0.6), ('Dos.', 0.0)]
    >>> [(b['text'], b['pause']) for b in segments('Uno. [pausa 1,5] Dos. [PAUSA 2s]')]
    [('Uno.', 1.5), ('Dos.', 2.0)]
    >>> [(b['text'], b['pause']) for b in segments('Uno.\\n\\n[pause 0.2]\\n\\nDos.')]
    [('Uno.', 0.2), ('Dos.', 0.0)]
    >>> [(b['text'], b['pause']) for b in segments('Uno.\\n \\n[pausa 1] [pause 2]\\nDos.')]
    [('Uno.', 3.0), ('Dos.', 0.0)]
    >>> [b['pause'] for b in segments('a' * 200 + '. ' + 'b' * 200 + '.')]
    [0.25, 0.0]
    >>> segments('[pausa 1]\\n\\n')
    []
    >>> [(b['text'], b['style'], b['emotion'])
    ...  for b in segments('Uno. [estilo: dramatica] Dos. [emocion: miedo 0.4] Tres.')]
    [('Uno.', 'expert', None), ('Dos.', 'dramatic', None), ('Tres.', 'dramatic', ('fear', 0.4))]
    >>> [(b['text'], b['style']) for b in segments('Uno.', 'soft')]
    [('Uno.', 'soft')]
    >>> [b['notices'] for b in segments('Hola, [estilo: intima] adiós.')]
    [['style change mid-sentence'], []]
    >>> [(b['text'], b['emotion']) for b in segments('Uno.\\n\\n[emocion: triste]Dos. [emotion:]Tres.')]
    [('Uno.', None), ('Dos.', ('sad', 0.6)), ('Tres.', None)]
    """
    text = normalize(text)
    out: list[dict] = []
    marks, has_mark, blank, pos = 0.0, False, False, 0
    current, emo = ALIAS_STYLES.get(style, style), None
    for m in [*MARK_BLOCK.finditer(text), None]:
        end = m.start() if m else len(text)
        previous = text[pos:end]
        for t in chunks(previous):
            if out:
                out[-1]['pause'] = marks if has_mark else PAUSE_PARAGRAPH if blank else PAUSE_SEG
            out.append(dict(text=t, pause=0.0, style=current, emotion=emo, notices=[]))
            marks, has_mark, blank = 0.0, False, False
        if m is None:
            break
        if m[1]:
            marks, has_mark = marks + float(m[1].replace(',', '.')), True
        elif m[2] is not None or m[3] is not None:
            if out and previous.strip() and not re.search(r'[.!?…:]\s*$', previous):
                kind = 'style' if m[2] is not None else 'emotion'
                out[-1]['notices'].append(f'{kind} change mid-sentence')
            if m[2] is not None:
                current = ALIAS_STYLES.get(m[2], m[2])
            else:
                emo = (
                    (ALIAS_EMOTIONS.get(m[3].lower(), m[3].lower()), float(m[4].replace(',', '.')) if m[4] else 0.6)
                    if m[3]
                    else None
                )
        else:
            blank = True
        pos = m.end()
    if out and has_mark:
        out[-1]['pause'] = marks
    return out


def tags(text: str) -> list[str]:
    """Marcas que el modelo pronunciaría. Las de la gramática (pausa, estilo, emoción, gestos, énfasis) no cuentan.

    >>> tags('Hola [breath] <break time="1s"/> **ojo** (pausa) [pausa 1]')
    ['[breath]', '<break time="1s"/>', '**', '(pause)']
    >>> tags('Texto limpio, con pausa.\\n\\nY otro párrafo.')
    []
    >>> tags('[risa] [estilo: dramatica] [emocion: triste 0.4] [enfasis]sí[/enfasis] [respiro]')
    []
    """
    return list(dict.fromkeys(LABEL.findall(NO_MARKS.sub(' ', normalize(text)))))
