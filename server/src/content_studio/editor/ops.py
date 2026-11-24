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
        self.code, self.params = code, params or {}


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
    old_start, requested = clip['start'], float(op['start'])
    group = _linked(doc, clip)
    destinations = [(member, op['track'] if member is clip else member['track']) for member in group]
    obstacles = {
        track: [other for other in doc['clips'] if other not in group and other['track'] == track]
        for _, track in destinations
    }
    others = [other for items in obstacles.values() for other in items]
    edges = [0.0, requested]
    edges.extend(other['start'] + clip_length(other) for other in others)
    for member, track in destinations:
        edges.extend(other['start'] - clip_length(member) for other in obstacles[track])
    free = [
        t
        for t in edges
        if t >= 0
        and all(
            not _overlaps(t, clip_length(member), other) for member, track in destinations for other in obstacles[track]
        )
    ]
    end = max((other['start'] + clip_length(other) for other in others), default=0.0)
    if not free:
        free = [end]
    start = min(free, key=lambda t: (abs(t - requested), t))
    delta = start - old_start
    for member, track in destinations:
        member.update(track=track, start=member['start'] + delta)


def set_track(doc: Doc, op: Op) -> None:
    """Actualiza volumen, mute, solo o bloqueo de una pista existente."""
    track = next((item for item in doc['tracks'] if item['id'] == op['id']), None)
    if track is None:
        raise OpError('unknown_track', {'id': op['id']})
    track.update(op['changes'])


def add_clip(doc: Doc, op: Op) -> None:
    """Agrega una copia de un clip importado o grabado."""
    doc['clips'].append(copy.deepcopy(op['clip']))


def set_fade(doc: Doc, op: Op) -> None:
    """Actualiza uno o ambos fundidos del clip."""
    clip = _find(doc, op['id'])
    for edge in ('fade_in', 'fade_out'):
        if edge in op:
            clip[edge] = float(op[edge])


def set_gain(doc: Doc, op: Op) -> None:
    """Actualiza la ganancia del clip en decibeles."""
    _find(doc, op['id'])['gain_db'] = float(op['gain_db'])


def add_track(doc: Doc, op: Op) -> None:
    """Inserta una pista de audio en el índice pedido o al final."""
    track = copy.deepcopy(op['track'])
    if any(item['id'] == track['id'] for item in doc['tracks']):
        raise OpError('duplicate_id', {'id': track['id']})
    index = max(0, min(int(op.get('index', len(doc['tracks']))), len(doc['tracks'])))
    doc['tracks'].insert(index, track)


def remove_track(doc: Doc, op: Op) -> None:
    """Quita una pista y sus clips."""
    if not any(track['id'] == op['id'] for track in doc['tracks']):
        raise OpError('unknown_track', {'id': op['id']})
    doc['tracks'] = [track for track in doc['tracks'] if track['id'] != op['id']]
    removed = [clip for clip in doc['clips'] if clip['track'] == op['id']]
    links = {clip.get('link') for clip in removed if clip.get('link')}
    doc['clips'] = [clip for clip in doc['clips'] if clip['track'] != op['id']]
    for clip in doc['clips']:
        if clip.get('link') in links:
            clip.pop('link')
    removed_ids = {clip['id'] for clip in removed}
    doc['transitions'] = [
        transition for transition in doc.get('transitions', []) if not {transition['a'], transition['b']} & removed_ids
    ]


def reorder_tracks(doc: Doc, op: Op) -> None:
    """Mueve una pista al índice visual indicado, limitado al rango de pistas."""
    index = next((i for i, track in enumerate(doc['tracks']) if track['id'] == op['id']), None)
    if index is None:
        raise OpError('unknown_track', {'id': op['id']})
    track = doc['tracks'].pop(index)
    destination = max(0, min(int(op['index']), len(doc['tracks'])))
    doc['tracks'].insert(destination, track)


def add_marker(doc: Doc, op: Op) -> None:
    """Agrega un marcador al proyecto."""
    doc['markers'].append(copy.deepcopy(op['marker']))


def move_marker(doc: Doc, op: Op) -> None:
    """Mueve un marcador a otro tiempo."""
    marker = next((item for item in doc['markers'] if item['id'] == op['id']), None)
    if marker is None:
        raise OpError('unknown_marker', {'id': op['id']})
    marker['t'] = float(op['t'])


def rename_marker(doc: Doc, op: Op) -> None:
    """Renombra un marcador existente."""
    marker = next((item for item in doc['markers'] if item['id'] == op['id']), None)
    if marker is None:
        raise OpError('unknown_marker', {'id': op['id']})
    marker['label'] = op['label']


def delete_marker(doc: Doc, op: Op) -> None:
    """Quita el marcador con ese id, si todavía existe."""
    doc['markers'] = [marker for marker in doc['markers'] if marker['id'] != op['id']]


def replace_source(doc: Doc, op: Op) -> None:
    """Reasigna todas las instancias de una fuente compartida."""
    for clip in doc['clips']:
        if clip['src'] == op['from']:
            clip['src'] = op['to']


def trim_clip(doc: Doc, op: Op) -> None:
    """Recorta un borde del clip hasta el tiempo `t`: el inicio mueve `start` y `src_in`; el final cambia `src_out`."""
    clip = _find(doc, op['id'])
    group = _linked(doc, clip)
    edge, t = op['edge'], float(op['t'])
    if edge == 'start':
        delta = t - clip['start']
        if any(member['src_in'] + delta * member.get('speed', 1) < 0 for member in group):
            raise OpError('bad_trim', {'id': clip['id']})
        for member in group:
            member.update(start=member['start'] + delta, src_in=member['src_in'] + delta * member.get('speed', 1))
    elif edge == 'end':
        length = t - clip['start']
        if length <= 0:
            raise OpError('bad_trim', {'id': clip['id']})
        for member in group:
            member['src_out'] = member['src_in'] + length * member.get('speed', 1)
    else:
        raise OpError('unknown_edge', {'edge': edge})


def split_at(doc: Doc, op: Op) -> None:
    """Corta en `t` cada clip que lo cruza (o solo los de `ids`). La mitad derecha se llama `<id>-r`."""
    t, only = float(op['t']), set(op['ids']) if op.get('ids') is not None else None
    if only is not None:
        for clip in doc['clips']:
            if clip['id'] in only and clip.get('link'):
                only.update(member['id'] for member in doc['clips'] if member.get('link') == clip['link'])
    for clip in list(doc['clips']):
        if only is not None and clip['id'] not in only:
            continue
        if not clip['start'] < t < clip['start'] + clip_length(clip):
            continue
        source_left = (t - clip['start']) * clip.get('speed', 1)
        right = {**clip, 'id': f'{clip["id"]}-r', 'start': t, 'src_in': clip['src_in'] + source_left, 'fade_in': 0}
        clip.update(src_out=clip['src_in'] + source_left, fade_out=0)
        doc['clips'].append(right)


def delete_clips(doc: Doc, op: Op) -> None:
    """Borra los clips de `ids`. Con `ripple`, los clips que venían después en su pista se corren hacia atrás."""
    ids = set(op['ids'])
    for clip in doc['clips']:
        if clip['id'] in ids and clip.get('link'):
            ids.update(member['id'] for member in doc['clips'] if member.get('link') == clip['link'])
    gone = [clip for clip in doc['clips'] if clip['id'] in ids]
    doc['clips'] = [clip for clip in doc['clips'] if clip['id'] not in ids]
    doc['transitions'] = [
        transition
        for transition in doc.get('transitions', [])
        if transition['a'] not in ids and transition['b'] not in ids
    ]
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


def link_clips(doc: Doc, op: Op) -> None:
    """Enlaza dos o más clips bajo el identificador indicado, limpiando los grupos anteriores."""
    ids = list(dict.fromkeys(op['ids']))
    if len(ids) < 2 or not op.get('link'):
        raise OpError('bad_link')
    selected = [_find(doc, clip_id) for clip_id in ids]
    old_links = {clip.get('link') for clip in selected if clip.get('link')}
    for clip in doc['clips']:
        if clip.get('link') in old_links:
            clip.pop('link')
    for clip in selected:
        clip['link'] = op['link']


def unlink_clips(doc: Doc, op: Op) -> None:
    """Desenlaza los grupos de los clips elegidos completos, para no dejar parejas huérfanas."""
    selected = [_find(doc, clip_id) for clip_id in op['ids']]
    links = {clip.get('link') for clip in selected if clip.get('link')}
    for clip in doc['clips']:
        if clip.get('link') in links:
            clip.pop('link')


def _find(doc: Doc, clip_id: str) -> Doc:
    """El clip con ese id; si no existe, un error del catálogo."""
    for clip in doc['clips']:
        if clip['id'] == clip_id:
            return clip
    raise OpError('unknown_clip', {'id': clip_id})


def _linked(doc: Doc, clip: Doc) -> list[Doc]:
    """Devuelve el clip y los otros que comparten su enlace, si existe."""
    link = clip.get('link')
    return [item for item in doc['clips'] if item.get('link') == link] if link else [clip]


def _overlaps(start: float, length: float, other: Doc) -> bool:
    """Si un clip que empieza en `start` y dura `length` se cruza con `other` en el tiempo."""
    return start < other['start'] + clip_length(other) and other['start'] < start + length


HANDLERS: dict[str, Callable[[Doc, Op], None]] = {
    'addClip': add_clip,
    'addTrack': add_track,
    'addMarker': add_marker,
    'deleteMarker': delete_marker,
    'moveClip': move_clip,
    'moveMarker': move_marker,
    'renameMarker': rename_marker,
    'removeTrack': remove_track,
    'reorderTracks': reorder_tracks,
    'replaceSource': replace_source,
    'setFade': set_fade,
    'setGain': set_gain,
    'setTrack': set_track,
    'trimClip': trim_clip,
    'splitAt': split_at,
    'deleteClips': delete_clips,
    'crossfade': crossfade,
    'linkClips': link_clips,
    'unlinkClips': unlink_clips,
}
