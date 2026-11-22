"""El proyecto de mezcla (spec 016, D-3): su `mix.json` en disco, los tramos de voz de su transcripción y su curva."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_studio.common import ffmpeg as ff
from content_studio.mix import envelope

DEFAULT_PARAMS: dict[str, Any] = {
    'mode': 'transcript',
    'duck_db': -12.0,
    'ramp_ms': 300,
    'music_db': -6.0,
    'voice_db': 0.0,
    'intro': 0.0,
    'outro': 0.0,
    'lufs': -14.0,
    'merge_gap': 0.6,
    'pre': 0.2,
    'post': 0.4,
}


def new_document(
    voice: str, music: str, video: str | None, video_mode: str, transcribe_job: int | None
) -> dict[str, Any]:
    """El `mix.json` de un proyecto nuevo, con los parámetros por defecto y sin regiones todavía."""
    return {
        'voice': voice,
        'music': music,
        'video': video,
        'video_mode': video_mode,
        'transcribe_job': transcribe_job,
        'regions': [],
        'params': dict(DEFAULT_PARAMS),
    }


def load(path: Path) -> dict[str, Any]:
    """El documento del proyecto."""
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, doc: dict[str, Any]) -> None:
    """Escribe el documento del proyecto."""
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')


def speech_regions(words_file: Path, params: dict[str, Any]) -> list[list[float]]:
    """Los tramos de voz de una transcripción (`segments` → `words`), con la unión y los márgenes de los parámetros."""
    transcript = json.loads(words_file.read_text(encoding='utf-8'))
    words = [(word['start'], word['end']) for segment in transcript['segments'] for word in segment['words']]
    regions = envelope.speech_regions(words, params['merge_gap'], params['pre'], params['post'])
    return [list(region) for region in regions]


def timeline(doc: dict[str, Any]) -> tuple[float, float]:
    """La duración de la mezcla y el desplazamiento de la voz. En `under` la mezcla es el video entero, sin intro."""
    if doc['video'] and doc['video_mode'] == 'under':
        return ff.probe_duration(doc['video']), 0.0
    intro, outro = doc['params']['intro'], doc['params']['outro']
    return intro + ff.probe_duration(doc['voice']) + outro, intro


def curve(doc: dict[str, Any]) -> dict[str, Any]:
    """La curva de ducking del proyecto: su duración `total` y los puntos [segundos, dB]."""
    total, shift = timeline(doc)
    params = doc['params']
    regions = [(start + shift, end + shift) for start, end in doc['regions']]
    points = envelope.gain_curve(regions, total, params['duck_db'], params['ramp_ms'] / 1000)
    return {'total': round(total, 3), 'points': [[t, db] for t, db in points]}
