"""Texto por turnos (spec 036, AC-6): un bloque por cambio de hablante, con su nombre y, si se pide, su hora."""

from content_studio.diarization.transcript_text import transcript_text

SPEAKERS = {
    'SPEAKER_00': {'name': 'Hablante 1', 'color': '#2563eb'},
    'SPEAKER_01': {'name': 'Hablante 2', 'color': '#dc2626'},
}
PAYLOAD = {
    'segments': [
        {
            'start': 0.0,
            'end': 1.0,
            'words': [
                {'start': 0.0, 'end': 0.5, 'word': ' hola', 'speaker': 'SPEAKER_00'},
                {'start': 0.6, 'end': 1.0, 'word': ' amigo', 'speaker': 'SPEAKER_00'},
            ],
        },
        {
            'start': 2.5,
            'end': 3.0,
            'words': [{'start': 2.5, 'end': 3.0, 'word': ' mundo', 'speaker': 'SPEAKER_01'}],
        },
    ]
}


def test_ac6_text_has_one_block_per_speaker_turn():
    """AC-6: un bloque por turno con su nombre; con marcas de tiempo, [hh:mm:ss] al inicio de cada bloque."""
    assert transcript_text(PAYLOAD, SPEAKERS, timestamps=True) == (
        '[00:00:00] Hablante 1: hola amigo\n[00:00:02] Hablante 2: mundo\n'
    )
    assert transcript_text(PAYLOAD, SPEAKERS, timestamps=False) == 'Hablante 1: hola amigo\nHablante 2: mundo\n'


def test_ac6_without_speakers_one_line_per_segment():
    """AC-6: sin hablantes, una línea por segmento y sin nombre."""
    plain = {
        'segments': [
            {'start': 0.0, 'end': 1.0, 'text': 'hola amigo', 'words': []},
            {'start': 2.5, 'end': 3.0, 'text': 'mundo', 'words': []},
        ]
    }

    assert transcript_text(plain, {}, timestamps=False) == 'hola amigo\nmundo\n'
    assert transcript_text(plain, {}, timestamps=True) == '[00:00:00] hola amigo\n[00:00:02] mundo\n'
