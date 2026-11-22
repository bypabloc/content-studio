"""Traducir al inglés (spec 014, D-8; AC-12): los segmentos de whisper pasan a `tracks.en` y a `.en.srt` y `.en.vtt`.

Whisper en modo traducción no da tiempos por palabra: cada segmento es un cue con sus tiempos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_studio.subtitles.document import load, save
from content_studio.subtitles.formats import to_srt, to_vtt


def cues_from_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Un cue por segmento, con sus tiempos y el texto sin espacios; los segmentos vacíos no entran."""
    cues: list[dict[str, Any]] = []
    for segment in segments:
        text = segment['text'].strip()
        if text:
            cues.append({'id': len(cues) + 1, 'start': segment['start'], 'end': segment['end'], 'text': text})
    return cues


def finish(doc_path: Path, out: Path) -> None:
    """Guarda `tracks.en` en el documento y exporta `<nombre>.en.srt` y `.en.vtt` en la carpeta del trabajo."""
    doc = load(doc_path)
    transcript = json.loads((out / 'words.json').read_text(encoding='utf-8'))
    english = {'cues': cues_from_segments(transcript['segments'])}
    doc['tracks'] = {**doc.get('tracks', {}), 'en': english['cues']}
    save(doc, doc_path)
    stem = Path(doc['source']['path']).stem
    (out / f'{stem}.en.srt').write_text(to_srt(english), encoding='utf-8')
    (out / f'{stem}.en.vtt').write_text(to_vtt(english), encoding='utf-8')
