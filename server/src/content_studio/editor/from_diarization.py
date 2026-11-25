"""Proyecto del Editor desde una diarización (spec 037, AC-6): el audio entero en la pista 1 y un marcador por turno."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from content_studio.editor import store

MIN_TURN = 0.5
DEFAULT_COLOR = '#64748b'


def project_from_diarization(
    source: str,
    duration: float,
    exclusive_turns: list[dict[str, Any]],
    speakers: dict[str, dict[str, str]],
    min_turn: float = MIN_TURN,
) -> dict[str, Any]:
    """El documento del esquema v3 con el audio como clip y un marcador por turno de `min_turn` segundos o más.

    El marcador lleva el nombre y el color del hablante, y su tiempo es el inicio del turno. Los turnos más cortos
    no llevan marcador: un «ajá» no merece una marca en la línea de tiempo.
    """
    doc = store.new_doc(Path(source).stem)
    track = doc['tracks'][0]['id']
    doc['clips'].append(
        {
            'id': 'c1',
            'track': track,
            'src': source,
            'src_in': 0,
            'src_out': duration,
            'start': 0,
            'fade_in': 0,
            'fade_out': 0,
            'speed': 1,
            'gain_db': 0,
        }
    )
    kept = [turn for turn in exclusive_turns if turn['end'] - turn['start'] >= min_turn]
    doc['markers'] = [
        {
            'id': f'm{index}',
            't': turn['start'],
            'label': speakers.get(turn['speaker'], {}).get('name', turn['speaker']),
            'color': speakers.get(turn['speaker'], {}).get('color', DEFAULT_COLOR),
        }
        for index, turn in enumerate(kept, start=1)
    ]
    return doc
