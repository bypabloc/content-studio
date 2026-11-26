"""Asignación de hablante a cada palabra (spec 035, AC-1)."""

from content_studio.diarization import assign

TURNS = [
    {'start': 0.0, 'end': 2.0, 'speaker': 'SPEAKER_00'},
    {'start': 2.0, 'end': 4.0, 'speaker': 'SPEAKER_01'},
    {'start': 6.0, 'end': 8.0, 'speaker': 'SPEAKER_00'},
]


def test_ac1_overlap_gap_and_far_words():
    """AC-1: el hablante con más solape gana; a 1 s o menos de un turno toma el más cercano; más lejos, None."""
    words = [
        {'start': 1.5, 'end': 2.7, 'word': 'solape'},
        {'start': 4.2, 'end': 4.6, 'word': 'hueco'},
        {'start': 5.2, 'end': 5.5, 'word': 'cerca'},
        {'start': 9.5, 'end': 9.8, 'word': 'lejos'},
        {'start': 0.5, 'word': 'sin_fin'},
    ]

    result = assign.assign_speakers(words, TURNS)

    assert [word['speaker'] for word in result] == ['SPEAKER_01', 'SPEAKER_01', 'SPEAKER_00', None, 'SPEAKER_00']
    assert result[0]['word'] == 'solape'


def test_ac1_without_turns_no_word_has_a_speaker():
    """AC-1: sin turnos, cada palabra sale con speaker None."""
    words = [{'start': 0.0, 'end': 1.0, 'word': 'hola'}]

    assert assign.assign_speakers(words, []) == [{'start': 0.0, 'end': 1.0, 'word': 'hola', 'speaker': None}]


def test_segment_speaker_doctest_examples():
    """El hablante de un segmento es el de más duración."""
    words = [{'start': 0, 'end': 1, 'speaker': 'A'}, {'start': 1, 'end': 3, 'speaker': 'B'}]

    assert assign.segment_speaker(words) == 'B'
