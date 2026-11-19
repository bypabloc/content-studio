"""Guiones de entrada (--texto, .txt y .json) y la salida .wav de cada uno, validada antes de cargar el modelo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content_studio import rutas
from content_studio.narration.estilos import ESTILOS


def leer_json(d: dict) -> tuple[str, str | None]:
    """Texto y estilo de un guion JSON. Cada elemento de `texto` es un párrafo. Un párrafo puede ser un
    objeto {"texto", "estilo", "emocion"}: equivale a anteponer esas marcas al texto.

    >>> leer_json({'texto': ['Uno.', 'Dos.'], 'estilo': 'suave'})
    ('Uno.\\n\\nDos.', 'suave')
    >>> leer_json({'texto': 'Solo uno.'})
    ('Solo uno.', None)
    >>> leer_json({'texto': ['Uno.', {'texto': 'Dos.', 'estilo': 'dramatica', 'emocion': 'miedo 0.4'}]})
    ('Uno.\\n\\n[estilo: dramatica][emocion: miedo 0.4]Dos.', None)
    """
    t = d['texto']
    if isinstance(t, str):
        return t, d.get('estilo')
    partes = []
    for p in t:
        if isinstance(p, dict):
            marcas = (f'[estilo: {p["estilo"]}]' if 'estilo' in p else '') + (
                f'[emocion: {p["emocion"]}]' if 'emocion' in p else ''
            )
            p = marcas + p['texto']
        partes.append(p)
    return '\n\n'.join(partes), d.get('estilo')


def guiones(a: argparse.Namespace) -> list[tuple[str | None, str, str | None]]:
    """(nombre de salida o None, texto, estilo del JSON o None) de --texto y de cada --archivo."""
    out = [(None, a.texto, None)] if a.texto else []
    for f in a.archivo or []:
        if f.suffix == '.json':
            d = json.loads(f.read_text(encoding='utf-8'))
            out.append((d.get('id', f.stem), *leer_json(d)))
        else:
            out.append((f.stem, f.read_text(encoding='utf-8'), None))
    return out


def planificar(a: argparse.Namespace, guiones: list[tuple]) -> list[tuple[str, str, Path]]:
    """(texto, estilo, salida .wav) de cada guion. Con un solo guion, --salida es el .wav, salvo que sea una carpeta
    (existe como tal o no tiene extensión). Falla antes de generar si la ruta no es .wav o dos guiones chocan.

    >>> from argparse import Namespace
    >>> a = Namespace(estilo=None, idioma='es', modelo='qwen-0.6b', salida=Path('out/lote'))
    >>> [s.as_posix() for *_, s in planificar(a, [(None, 'Hola', None)])]
    ['out/lote/qwen-0.6b-experta.wav']
    >>> a.salida = Path('x.mp3'); planificar(a, [('a', 'Hola', None)])
    Traceback (most recent call last):
    SystemExit: --salida x.mp3: tiene que ser un .wav o una carpeta
    >>> a.salida = None; len(planificar(a, [('a', 'Uno', None), ('a', 'Dos', 'suave')]))
    Traceback (most recent call last):
    SystemExit: Dos guiones van al mismo archivo: a-qwen-0.6b.wav (usa ids distintos)
    """
    archivo = len(guiones) == 1 and a.salida and a.salida.suffix and not a.salida.is_dir()
    if archivo and a.salida.suffix.lower() != '.wav':
        sys.exit(f'--salida {a.salida}: tiene que ser un .wav o una carpeta')
    trabajos = []
    for nombre, texto, estilo_json in guiones:
        estilo = a.estilo or estilo_json or ('neutral-en' if a.idioma == 'en' else 'experta')
        if estilo not in ESTILOS:
            sys.exit(f'Estilo desconocido "{estilo}" en {nombre}. Opciones: {", ".join(ESTILOS)}')
        if archivo:
            salida = a.salida
        else:
            wav = f'{nombre}-{a.modelo}.wav' if nombre else f'{a.modelo}-{estilo}.wav'
            salida = (a.salida or rutas.OUT / 'narration') / wav
        if any(s == salida for *_, s in trabajos):
            sys.exit(f'Dos guiones van al mismo archivo: {salida.name} (usa ids distintos)')
        trabajos.append((texto, estilo, salida))
    return trabajos


def avisar_sobrescritura(trabajos: list[tuple[str, str, Path]]) -> None:
    """Las tomas pisan el .wav y el .json anteriores: se avisa antes de cargar el modelo, sin cambiar la ruta."""
    for *_, salida in trabajos:
        if salida.exists():
            print(f'Aviso: sobrescribe {salida} y su .json', file=sys.stderr)
