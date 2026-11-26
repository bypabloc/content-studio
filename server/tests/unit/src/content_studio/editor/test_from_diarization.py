"""Proyecto del Editor desde una diarización (spec 037, AC-6): el audio como clip y un marcador por turno."""

from __future__ import annotations

from content_studio.editor.from_diarization import project_from_diarization
from content_studio.editor.project import validate

TURNS = [
    {'start': 0.0, 'end': 1.0, 'speaker': 'SPEAKER_00'},
    {'start': 1.0, 'end': 1.3, 'speaker': 'SPEAKER_01'},
    {'start': 2.0, 'end': 4.0, 'speaker': 'SPEAKER_01'},
]
SPEAKERS = {
    'SPEAKER_00': {'name': 'Ana', 'color': '#2563eb'},
    'SPEAKER_01': {'name': 'Luis', 'color': '#dc2626'},
}


def test_ac6_clip_and_markers():
    """AC-6: el audio como clip de la pista de audio y un marcador por turno de 0,5 s o más, en un proyecto válido."""
    doc = project_from_diarization('C:/in/charla.wav', 4.0, TURNS, SPEAKERS)

    assert validate(doc) == []
    (clip,) = doc['clips']
    audio = next(track for track in doc['tracks'] if track['kind'] == 'audio')
    assert clip['track'] == audio['id']
    assert clip['src'] == 'C:/in/charla.wav'
    assert (clip['src_in'], clip['src_out'], clip['start']) == (0, 4.0, 0)
    assert [(marker['t'], marker['label']) for marker in doc['markers']] == [(0.0, 'Ana'), (2.0, 'Luis')]
