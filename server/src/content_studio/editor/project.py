"""Modelo del proyecto del editor (spec 018, D-1): migración v1→v2, validación y duración. Puro, solo stdlib."""

from __future__ import annotations

import copy
import math
from typing import Any, TypeGuard

VERSION = 2
SAMPLE_RATE = 48000
DEFAULT_CANVAS = {'width': 1920, 'height': 1080, 'fps': 30, 'background': '#000000'}
EASES = {'linear', 'ease-in-out', 'hold'}
# cspell:ignore fadeblack fadewhite wipeleft wiperight slideleft slideright circleopen: transiciones de FFmpeg
TRANSITIONS = {'fade', 'fadeblack', 'fadewhite', 'wipeleft', 'wiperight', 'slideleft', 'slideright', 'circleopen'}
TRANSFORM_KEYS = {'x', 'y', 'scale_x', 'scale_y', 'rotation', 'opacity', 'anchor_x', 'anchor_y'}
KEYFRAME_KEYS = TRANSFORM_KEYS | {'crop_l', 'crop_t', 'crop_r', 'crop_b'}

Doc = dict[str, Any]


def migrate(doc: Doc) -> Doc:
    """Devuelve un documento actual sin mutar ni perder campos de la v1."""
    version = doc.get('version')
    if version not in {1, VERSION}:
        raise ValueError(f'unsupported project version: {version!r}')
    result = copy.deepcopy(doc)
    if version == 1:
        result['version'] = VERSION
        result.setdefault('canvas', copy.deepcopy(DEFAULT_CANVAS))
    result.setdefault('transitions', [])
    for track in result.get('tracks', []):
        track.setdefault('kind', 'audio')
    return result


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
    """Los errores del documento: código y id de la entidad inválida. Lista vacía si es válido."""
    tracks = {track['id']: track for track in doc['tracks']}
    clips = {clip['id']: clip for clip in doc['clips']}
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    reported: set[str] = set()
    for clip in doc['clips']:
        clip_id = clip['id']
        if clip_id in seen and clip_id not in reported:
            errors.append({'code': 'duplicate_id', 'id': clip_id})
            reported.add(clip_id)
        seen.add(clip_id)
        errors.extend(_clip_errors(clip, tracks))
    if doc.get('version') == VERSION:
        errors.extend(_transition_errors(doc.get('transitions', []), clips, tracks))
        errors.extend(_link_errors(doc['clips'], tracks))
    return errors


def _clip_errors(clip: Doc, tracks: dict[str, Doc]) -> list[dict[str, str]]:
    """Los errores de un clip, incluidos el tipo de pista y sus datos visuales."""
    clip_id = clip['id']
    found: list[dict[str, str]] = []
    track = tracks.get(clip['track'])
    if track is None:
        found.append({'code': 'unknown_track', 'id': clip_id})
    elif (track.get('kind', 'audio') == 'video') != ('media' in clip):
        found.append({'code': 'wrong_track_kind', 'id': clip_id})
    if clip['start'] < 0:
        found.append({'code': 'negative_start', 'id': clip_id})
    if clip['src_in'] < 0 or clip['src_out'] <= clip['src_in']:
        found.append({'code': 'bad_source_range', 'id': clip_id})
    if clip['fade_in'] + clip['fade_out'] > clip_length(clip):
        found.append({'code': 'fade_too_long', 'id': clip_id})
    if 'media' in clip:
        found.extend(_visual_errors(clip))
    return found


def _visual_errors(clip: Doc) -> list[dict[str, str]]:
    """Valida formato, transformación y keyframes de un clip visual."""
    clip_id = clip['id']
    found: list[dict[str, str]] = []
    transform = clip.get('transform')
    if clip['media'] not in ('video', 'image') or not isinstance(transform, dict):
        return [{'code': 'bad_transform', 'id': clip_id}]
    crop = transform.get('crop')
    if not isinstance(crop, dict):
        return [{'code': 'bad_transform', 'id': clip_id}]
    values = [transform.get(key) for key in TRANSFORM_KEYS]
    valid = all(_finite_number(value) for value in values)
    crop_values: dict[str, int | float] = {}
    for edge in ('l', 't', 'r', 'b'):
        value = crop.get(edge)
        if not _finite_number(value) or not 0 <= value <= 1:
            valid = False
            break
        crop_values[edge] = value
    if valid:
        valid = (
            transform['scale_x'] > 0
            and transform['scale_y'] > 0
            and 0 <= transform['opacity'] <= 1
            and 0 <= transform['anchor_x'] <= 1
            and 0 <= transform['anchor_y'] <= 1
            and crop_values['l'] + crop_values['r'] < 1
            and crop_values['t'] + crop_values['b'] < 1
        )
    if not valid:
        found.append({'code': 'bad_transform', 'id': clip_id})
    keyframes = clip.get('keyframes')
    if not isinstance(keyframes, dict) or not _valid_keyframes(keyframes, clip_length(clip)):
        found.append({'code': 'bad_keyframes', 'id': clip_id})
    return found


def _valid_keyframes(keyframes: dict[str, Any], length: float) -> bool:
    """Si las propiedades tienen tiempos estrictos, valores finitos y curvas conocidas."""
    for prop, frames in keyframes.items():
        if prop not in KEYFRAME_KEYS or not isinstance(frames, list):
            return False
        previous = -1.0
        for frame in frames:
            if not isinstance(frame, dict):
                return False
            t, value, ease = frame.get('t'), frame.get('value'), frame.get('ease')
            if not _finite_number(t) or not _finite_number(value) or not 0 <= t <= length:
                return False
            if t <= previous or not isinstance(ease, str) or ease not in EASES:
                return False
            previous = t
    return True


def _transition_errors(transitions: list[Doc], clips: dict[str, Doc], tracks: dict[str, Doc]) -> list[dict[str, str]]:
    """Una transición une dos clips visuales contiguos de su misma pista."""
    found: list[dict[str, str]] = []
    for transition in transitions:
        transition_id = transition.get('id', '')
        a_id, b_id, track_id = transition.get('a'), transition.get('b'), transition.get('track')
        a = clips.get(a_id) if isinstance(a_id, str) else None
        b = clips.get(b_id) if isinstance(b_id, str) else None
        track = tracks.get(track_id) if isinstance(track_id, str) else None
        if a is None or b is None or track is None or track.get('kind') != 'video':
            found.append({'code': 'bad_transition', 'id': transition_id})
            continue
        length_a, length_b = clip_length(a), clip_length(b)
        overlap = a['start'] + length_a - b['start']
        valid = (
            a['track'] == b['track'] == track_id
            and a.get('media') in {'video', 'image'}
            and b.get('media') in {'video', 'image'}
            and isinstance(transition.get('type'), str)
            and transition.get('type') in TRANSITIONS
            and _finite_number(transition.get('duration'))
            and 0 < transition['duration'] <= min(length_a, length_b)
            and math.isclose(overlap, transition['duration'], abs_tol=1e-9)
        )
        if not valid:
            found.append({'code': 'bad_transition', 'id': transition_id})
    return found


def _link_errors(clips: list[Doc], tracks: dict[str, Doc]) -> list[dict[str, str]]:
    """Cada grupo enlazado contiene un audio y un video con el mismo rango de tiempo."""
    groups: dict[str, list[Doc]] = {}
    for clip in clips:
        if clip.get('link'):
            groups.setdefault(clip['link'], []).append(clip)
    found: list[dict[str, str]] = []
    for link, group in groups.items():
        audio = [
            clip
            for clip in group
            if tracks.get(clip['track'], {}).get('kind', 'audio') == 'audio' and 'media' not in clip
        ]
        video = [clip for clip in group if clip.get('media') == 'video']
        valid = len(group) == 2 and len(audio) == 1 and len(video) == 1
        if valid:
            valid = math.isclose(audio[0]['start'], video[0]['start'], abs_tol=1e-9) and math.isclose(
                clip_length(audio[0]), clip_length(video[0]), abs_tol=1e-9
            )
        if not valid:
            found.append({'code': 'bad_link', 'id': link})
    return found


def _finite_number(value: Any) -> TypeGuard[int | float]:
    """Acepta enteros y flotantes finitos, pero no booleanos."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
