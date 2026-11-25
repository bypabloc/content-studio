"""Bloques de palabras por hablante y absorción de una palabra aislada (spec 035, AC-2)."""

from content_studio.diarization import blocks


def _word(start, end, speaker, text='x'):
    return {'start': start, 'end': end, 'word': text, 'speaker': speaker}


def test_ac2_splits_on_each_change_and_absorbs_isolated_word():
    """AC-2: B aislada entre dos bloques de A, con pausas menores a 0,3 s, se absorbe; C no se absorbe."""
    w1, w2 = _word(0.0, 0.4, 'A', 'hola'), _word(0.4, 0.8, 'A', 'mundo')
    w3 = _word(0.9, 1.0, 'B', 'eh')
    w4 = _word(1.2, 1.5, 'A', 'si')
    w5, w6 = _word(2.0, 2.4, 'B', 'ok'), _word(2.6, 2.9, 'C', 'x')

    result = blocks.blocks([w1, w2, w3, w4, w5, w6])

    assert result == [
        {'speaker': 'A', 'start': 0.0, 'end': 1.5, 'words': [w1, w2, w3, w4]},
        {'speaker': 'B', 'start': 2.0, 'end': 2.4, 'words': [w5]},
        {'speaker': 'C', 'start': 2.6, 'end': 2.9, 'words': [w6]},
    ]


def test_ac2_half_second_pause_is_not_absorbed():
    """AC-2: con pausa de 0,5 s, la palabra de B no se absorbe y forma su bloque."""
    words = [_word(0.0, 0.4, 'A'), _word(0.9, 1.0, 'B'), _word(1.6, 2.0, 'A')]

    assert [block['speaker'] for block in blocks.blocks(words)] == ['A', 'B', 'A']
