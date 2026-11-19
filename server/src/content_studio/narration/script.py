"""Guiones de entrada (--text, .txt y .json) y la salida .wav de cada uno, validada antes de cargar el modelo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content_studio import paths
from content_studio.narration.styles import STYLES
from content_studio.narration.text.segments import ALIAS_KEYS, ALIAS_STYLES


def _canonical(d: dict) -> dict:
    """Las claves del JSON en su forma canónica: texto -> text, estilo -> style, emocion -> emotion."""
    return {ALIAS_KEYS.get(k, k): v for k, v in d.items()}


def leer_json(d: dict) -> tuple[str, str | None]:
    """Texto y estilo de un guion JSON. Cada elemento de `text` es un párrafo. Un párrafo puede ser un objeto
    {"text", "style", "emotion"} (o sus alias "texto", "estilo", "emocion"): equivale a anteponer esas marcas al texto.

    >>> leer_json({'text': ['Uno.', 'Dos.'], 'style': 'soft'})
    ('Uno.\\n\\nDos.', 'soft')
    >>> leer_json({'text': 'Solo uno.'})
    ('Solo uno.', None)
    >>> leer_json({'text': ['Uno.', {'text': 'Dos.', 'style': 'dramatic', 'emotion': 'miedo 0.4'}]})
    ('Uno.\\n\\n[style: dramatic][emotion: miedo 0.4]Dos.', None)
    """
    d = _canonical(d)
    style = ALIAS_STYLES.get(d['style'], d['style']) if 'style' in d else None
    t = d['text']
    if isinstance(t, str):
        return t, style
    parts = []
    for p in t:
        if isinstance(p, dict):
            p = _canonical(p)
            marks = (f'[style: {ALIAS_STYLES.get(p["style"], p["style"])}]' if 'style' in p else '') + (
                f'[emotion: {p["emotion"]}]' if 'emotion' in p else ''
            )
            p = marks + p['text']
        parts.append(p)
    return '\n\n'.join(parts), style


def scripts(a: argparse.Namespace) -> list[tuple[str | None, str, str | None]]:
    """(nombre de salida o None, texto, estilo del JSON o None) de --text y de cada --file."""
    out = [(None, a.text, None)] if a.text else []
    for f in a.file or []:
        if f.suffix == '.json':
            d = json.loads(f.read_text(encoding='utf-8'))
            out.append((d.get('id', f.stem), *leer_json(d)))
        else:
            out.append((f.stem, f.read_text(encoding='utf-8'), None))
    return out


def plan(a: argparse.Namespace, scripts: list[tuple]) -> list[tuple[str, str, Path]]:
    """(texto, estilo, salida .wav) de cada guion. Con un solo guion, --output es el .wav, salvo que sea una carpeta
    (existe como tal o no tiene extensión). Falla antes de generar si la ruta no es .wav o dos guiones chocan.

    >>> from argparse import Namespace
    >>> a = Namespace(style=None, language='es', model='qwen-0.6b', output=Path('out/lote'))
    >>> [s.as_posix() for *_, s in plan(a, [(None, 'Hola', None)])]
    ['out/lote/qwen-0.6b-expert.wav']
    >>> a.output = Path('x.mp3'); plan(a, [('a', 'Hola', None)])
    Traceback (most recent call last):
    SystemExit: --output x.mp3: it must be a .wav or a folder
    >>> a.output = None; len(plan(a, [('a', 'Uno', None), ('a', 'Dos', 'soft')]))
    Traceback (most recent call last):
    SystemExit: Two scripts go to the same file: a-qwen-0.6b.wav (use different ids)
    """
    file = len(scripts) == 1 and a.output and a.output.suffix and not a.output.is_dir()
    if file and a.output.suffix.lower() != '.wav':
        sys.exit(f'--output {a.output}: it must be a .wav or a folder')
    jobs = []
    for name, text, style_json in scripts:
        style = a.style or style_json or ('neutral-en' if a.language == 'en' else 'expert')
        if style not in STYLES:
            sys.exit(f'Unknown style "{style}" in {name}. Options: {", ".join(STYLES)}')
        if file:
            output = a.output
        else:
            wav = f'{name}-{a.model}.wav' if name else f'{a.model}-{style}.wav'
            output = (a.output or paths.OUT / 'narration') / wav
        if any(s == output for *_, s in jobs):
            sys.exit(f'Two scripts go to the same file: {output.name} (use different ids)')
        jobs.append((text, style, output))
    return jobs


def warn_overwrite(jobs: list[tuple[str, str, Path]]) -> None:
    """Las tomas pisan el .wav y el .json anteriores: se avisa antes de cargar el modelo, sin cambiar la ruta."""
    for *_, output in jobs:
        if output.exists():
            print(f'Notice: overwrites {output} and its .json', file=sys.stderr)
