"""Traducir al inglés (014, D-8; AC-12) con la transcripción simulada: cues en inglés sobre los tiempos de whisper."""

from __future__ import annotations

import json

from content_studio.subtitles import translate
from content_studio.subtitles.document import load, save
from content_studio.subtitles.sources import from_cleaner

WORDS = [
    {'word': 'hola', 'start': 1.0, 'end': 1.4},
    {'word': 'mundo', 'start': 1.5, 'end': 2.5},
]
SEGMENTS = [
    {'start': 1.0, 'end': 2.5, 'text': ' Hello world. ', 'words': []},
    {'start': 3.0, 'end': 3.0, 'text': '   ', 'words': []},
    {'start': 4.0, 'end': 5.25, 'text': 'See you soon.', 'words': []},
]


def test_segments_become_english_cues_on_the_same_times():
    """AC-12: cada segmento de whisper es un cue en inglés con sus tiempos; los vacíos se descartan."""
    assert translate.cues_from_segments(SEGMENTS) == [
        {'id': 1, 'start': 1.0, 'end': 2.5, 'text': 'Hello world.'},
        {'id': 2, 'start': 4.0, 'end': 5.25, 'text': 'See you soon.'},
    ]


def test_finish_stores_the_track_and_exports_the_en_srt_and_vtt(tmp_path):
    """AC-12: `tracks.en` queda en el documento y `<nombre>.en.srt` y `.en.vtt` salen en la carpeta del trabajo."""
    doc_path = tmp_path / 'proyecto' / 'subtitles.json'
    save(from_cleaner(WORDS, source_path='clase.mp4', language='es'), doc_path)
    out = tmp_path / 'trabajo'
    out.mkdir()
    (out / 'words.json').write_text(json.dumps({'segments': SEGMENTS}), encoding='utf-8')

    translate.finish(doc_path, out)

    assert load(doc_path)['tracks']['en'][0]['text'] == 'Hello world.'
    assert '00:00:01,000 --> 00:00:02,500\nHello world.' in (out / 'clase.en.srt').read_text(encoding='utf-8')
    assert (out / 'clase.en.vtt').read_text(encoding='utf-8').startswith('WEBVTT')
