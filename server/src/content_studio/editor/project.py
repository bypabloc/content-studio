"""Modelo del proyecto del editor (spec 017, D-1): el esquema v1, su validación y su duración. Puro, solo stdlib.

Un clip usa el rango `src_in`–`src_out` de su fuente y se coloca en `start` de la línea de tiempo. Su duración en la
línea de tiempo es ese rango.
"""

from __future__ import annotations

from typing import Any

VERSION = 1
SAMPLE_RATE = 48000

Doc = dict[str, Any]


def migrate(doc: Doc) -> Doc:
    """Devuelve el documento en el esquema actual. La 018 agrega aquí los saltos de versión, sin perder campos."""
    if doc.get('version') != VERSION:
        raise ValueError(f'unsupported project version: {doc.get("version")!r}')
    return doc


def clip_length(clip: Doc) -> float:
    """La duración del clip en la línea de tiempo: el rango de su fuente.

    >>> clip_length({'src_in': 2, 'src_out': 6})
    4
    """
    return clip['src_out'] - clip['src_in']


def duration(doc: Doc) -> float:
    """El final del clip que más tarde termina; 0 sin clips.

    >>> duration({'clips': [{'start': 0, 'src_in': 0, 'src_out': 4}, {'start': 2, 'src_in': 0, 'src_out': 3}]})
    5
    """
    return max((clip['start'] + clip_length(clip) for clip in doc['clips']), default=0)


def validate(doc: Doc) -> list[dict[str, str]]:
    """Los errores del documento: código del catálogo e id del clip. Lista vacía si es válido.

    Un id repetido se reporta una vez. Los dos fades no pueden sumar más que la duración del clip.

    >>> validate({'tracks': [], 'clips': []})
    []
    """
    errors: list[dict[str, str]] = []
    tracks = {track['id'] for track in doc['tracks']}
    seen: set[str] = set()
    reported: set[str] = set()
    for clip in doc['clips']:
        clip_id = clip['id']
        if clip_id in seen and clip_id not in reported:
            errors.append({'code': 'duplicate_id', 'id': clip_id})
            reported.add(clip_id)
        seen.add(clip_id)
        errors.extend(_clip_errors(clip, tracks))
    return errors


def _clip_errors(clip: Doc, tracks: set[str]) -> list[dict[str, str]]:
    """Los errores de un clip que no dependen de los demás."""
    clip_id = clip['id']
    found: list[dict[str, str]] = []
    if clip['track'] not in tracks:
        found.append({'code': 'unknown_track', 'id': clip_id})
    if clip['start'] < 0:
        found.append({'code': 'negative_start', 'id': clip_id})
    if clip['src_in'] < 0 or clip['src_out'] <= clip['src_in']:
        found.append({'code': 'bad_source_range', 'id': clip_id})
    if clip['fade_in'] + clip['fade_out'] > clip_length(clip):
        found.append({'code': 'fade_too_long', 'id': clip_id})
    return found
