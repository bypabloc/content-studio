"""Operaciones puras sobre el documento del editor (spec 017, D-6). Cada una devuelve un documento nuevo.

El espejo en TypeScript (`client/src/features/editor/model/ops.ts`) implementa la misma semántica con estas fixtures.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from content_studio.editor.project import Doc, clip_length

Op = dict[str, Any]


class OpError(Exception):
    """Una operación que no se puede aplicar, con su código del catálogo."""

    def __init__(self, code: str, params: dict[str, Any] | None = None) -> None:
        """Guarda el código y sus parámetros."""
        super().__init__(code)
        self.code = code
        self.params = params or {}


def apply(doc: Doc, op: Op) -> Doc:
    """Aplica `op` a una copia de `doc`. `op['type']` nombra la operación.

    >>> apply({'clips': []}, {'type': 'nope'})
    Traceback (most recent call last):
    ...
    content_studio.editor.ops.OpError: unknown_op
    """
    handler = HANDLERS.get(op.get('type', ''))
    if handler is None:
        raise OpError('unknown_op', {'type': op.get('type')})
    result = copy.deepcopy(doc)
    handler(result, op)
    return result


def move_clip(doc: Doc, op: Op) -> None:
    """Mueve un clip a otra pista o a otro tiempo. En su pista no puede pisar a otro: queda pegado al hueco libre más
    cercano (el borde de un clip vecino o el inicio). Superponer en otra pista sí está permitido."""
    clip = _find(doc, op['id'])
    track, requested = op['track'], float(op['start'])
    others = [other for other in doc['clips'] if other is not clip and other['track'] == track]
    if not others:
        clip.update(track=track, start=max(0.0, requested))
        return
    length = clip_length(clip)
    edges = [0.0, requested, max(other['start'] + clip_length(other) for other in others)]
    edges += [other['start'] + clip_length(other) for other in others]
    edges += [other['start'] - length for other in others]
    free = [t for t in edges if t >= 0 and not any(_overlaps(t, length, o) for o in others)]
    clip.update(track=track, start=min(free, key=lambda t: (abs(t - requested), t)))


def set_track(doc: Doc, op: Op) -> None:
    """Actualiza volumen, mute, solo o bloqueo de una pista existente."""
    track = next((item for item in doc['tracks'] if item['id'] == op['id']), None)
    if track is None:
        raise OpError('unknown_track', {'id': op['id']})
    track.update(op['changes'])


def trim_clip(doc: Doc, op: Op) -> None:
    """Recorta un borde del clip hasta el tiempo `t`: el inicio mueve `start` y `src_in`; el final cambia `src_out`."""
    clip = _find(doc, op['id'])
    edge, t = op['edge'], float(op['t'])
    if edge == 'start':
        delta = t - clip['start']
        if clip['src_in'] + delta < 0:
            raise OpError('bad_trim', {'id': clip['id']})
        clip.update(start=t, src_in=clip['src_in'] + delta)
    elif edge == 'end':
        length = t - clip['start']
        if length <= 0:
            raise OpError('bad_trim', {'id': clip['id']})
        clip['src_out'] = clip['src_in'] + length
    else:
        raise OpError('unknown_edge', {'edge': edge})


def split_at(doc: Doc, op: Op) -> None:
    """Corta en `t` cada clip que lo cruza (o solo los de `ids`). La mitad derecha se llama `<id>-r`."""
    t, only = float(op['t']), op.get('ids')
    for clip in list(doc['clips']):
        if only is not None and clip['id'] not in only:
            continue
        if not clip['start'] < t < clip['start'] + clip_length(clip):
            continue
        left = t - clip['start']
        right = {**clip, 'id': f'{clip["id"]}-r', 'start': t, 'src_in': clip['src_in'] + left, 'fade_in': 0}
        clip.update(src_out=clip['src_in'] + left, fade_out=0)
        doc['clips'].append(right)


def delete_clips(doc: Doc, op: Op) -> None:
    """Borra los clips de `ids`. Con `ripple`, los clips que venían después en su pista se corren hacia atrás."""
    gone = [clip for clip in doc['clips'] if clip['id'] in op['ids']]
    doc['clips'] = [clip for clip in doc['clips'] if clip['id'] not in op['ids']]
    if not op.get('ripple', False):
        return
    for removed in sorted(gone, key=lambda clip: clip['start'], reverse=True):
        end = removed['start'] + clip_length(removed)
        for clip in doc['clips']:
            if clip['track'] == removed['track'] and clip['start'] >= end:
                clip['start'] -= clip_length(removed)


def crossfade(doc: Doc, op: Op) -> None:
    """Une `b` detrás de `a` con un cruce de `d` segundos: `b` empieza `d` antes del final de `a`, con fundido."""
    a, b, d = _find(doc, op['a']), _find(doc, op['b']), float(op['d'])
    b.update(start=a['start'] + clip_length(a) - d, fade_in=d)
    a['fade_out'] = d


def _find(doc: Doc, clip_id: str) -> Doc:
    """El clip con ese id; si no existe, un error del catálogo."""
    for clip in doc['clips']:
        if clip['id'] == clip_id:
            return clip
    raise OpError('unknown_clip', {'id': clip_id})


def _overlaps(start: float, length: float, other: Doc) -> bool:
    """Si un clip que empieza en `start` y dura `length` se cruza con `other` en el tiempo."""
    return start < other['start'] + clip_length(other) and other['start'] < start + length


HANDLERS: dict[str, Callable[[Doc, Op], None]] = {
    'moveClip': move_clip,
    'setTrack': set_track,
    'trimClip': trim_clip,
    'splitAt': split_at,
    'deleteClips': delete_clips,
    'crossfade': crossfade,
}
