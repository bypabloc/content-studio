"""Exportaciones de los turnos: RTTM, CSV y JSON (spec 035, AC-3)."""

import json

from content_studio.diarization import exports

TURNS = [
    {'start': 0.0, 'end': 2.5, 'speaker': 'SPEAKER_00'},
    {'start': 2.5, 'end': 4.25, 'speaker': 'SPEAKER_01'},
]
SPEAKERS = {
    'SPEAKER_00': {'name': 'Hablante 1', 'color': '#2563eb'},
    'SPEAKER_01': {'name': 'Hablante 2', 'color': '#dc2626'},
}


def test_ac3_rttm_has_one_line_per_turn():
    """AC-3: RTTM con inicio y duración de 3 decimales y los campos <NA>."""
    assert exports.rttm(TURNS, 'audio').splitlines() == [
        'SPEAKER audio 1 0.000 2.500 <NA> <NA> SPEAKER_00 <NA> <NA>',
        'SPEAKER audio 1 2.500 1.750 <NA> <NA> SPEAKER_01 <NA> <NA>',
    ]


def test_ac3_csv_carries_the_speaker_name():
    """AC-3: CSV con cabecera start,end,speaker,name."""
    assert exports.csv_text(TURNS, SPEAKERS).splitlines() == [
        'start,end,speaker,name',
        '0.000,2.500,SPEAKER_00,Hablante 1',
        '2.500,4.250,SPEAKER_01,Hablante 2',
    ]


def test_ac3_write_all_writes_json_rttm_and_csv(tmp_path):
    """AC-3: turns.json trae duration, speakers, diarization y exclusive_diarization."""
    result = {
        'duration': 4.25,
        'speakers': ['SPEAKER_00', 'SPEAKER_01'],
        'diarization': TURNS,
        'exclusive_diarization': TURNS,
    }

    exports.write_all(tmp_path, result, SPEAKERS)

    data = json.loads((tmp_path / 'turns.json').read_text(encoding='utf-8'))
    assert data == result
    assert (tmp_path / 'turns.rttm').read_text(encoding='utf-8').splitlines()[0].startswith('SPEAKER audio 1 0.000')
    assert (tmp_path / 'turns.csv').read_text(encoding='utf-8').splitlines()[0] == 'start,end,speaker,name'
