"""Formatos SRT y VTT (spec 014, D-3, AC-2): ida y vuelta sin perder texto ni tiempos, y lectura tolerante."""

from __future__ import annotations

from content_studio.subtitles.document import new_document
from content_studio.subtitles.formats import parse_srt, parse_vtt, to_srt, to_vtt


def _doc() -> dict:
    cues = [
        {
            'id': 1,
            'start': 0.0,
            'end': 2.5,
            'text': 'Hola mundo, esto es',
            'words': [
                {'start': 0.0, 'end': 0.4, 'text': 'Hola'},
                {'start': 0.5, 'end': 0.9, 'text': 'mundo,'},
                {'start': 1.0, 'end': 1.3, 'text': 'esto'},
                {'start': 1.4, 'end': 2.5, 'text': 'es'},
            ],
        },
        {
            'id': 2,
            'start': 3.001,
            'end': 4.75,
            'text': 'una prueba',
            'words': [
                {'start': 3.001, 'end': 3.5, 'text': 'una'},
                {'start': 3.6, 'end': 4.75, 'text': 'prueba'},
            ],
        },
    ]
    return new_document(source_path='entrada.wav', kind='file', language='es', cues=cues)


def _triples(doc: dict) -> list[tuple[float, float, str]]:
    return [(cue['start'], cue['end'], cue['text']) for cue in doc['cues']]


def _parsed_triples(cues: list[dict]) -> list[tuple[float, float, str]]:
    return [(cue['start'], cue['end'], cue['text']) for cue in cues]


def test_ac2_srt_round_trip_keeps_text_and_times_within_one_millisecond():
    """AC-2: parse_srt(to_srt(doc)) queda igual en texto y en tiempos (±1 ms)."""
    original = _triples(_doc())

    back = _parsed_triples(parse_srt(to_srt(_doc())))

    assert [text for _, _, text in back] == [text for _, _, text in original]
    for (start, end, _), (back_start, back_end, _) in zip(original, back, strict=True):
        assert abs(start - back_start) <= 0.001
        assert abs(end - back_end) <= 0.001


def test_ac2_vtt_round_trip_keeps_text_and_times_within_one_millisecond():
    """AC-2: lo mismo con VTT."""
    original = _triples(_doc())

    back = _parsed_triples(parse_vtt(to_vtt(_doc())))

    assert [text for _, _, text in back] == [text for _, _, text in original]
    for (start, end, _), (back_start, back_end, _) in zip(original, back, strict=True):
        assert abs(start - back_start) <= 0.001
        assert abs(end - back_end) <= 0.001


def test_ac2_vtt_starts_with_the_header_and_uses_dots_in_the_times():
    """El VTT empieza con WEBVTT y usa punto como separador de milisegundos."""
    text = to_vtt(_doc())

    assert text.startswith('WEBVTT\n')
    assert '00:00:00.000 --> 00:00:02.500' in text


def test_ac2_parse_srt_accepts_a_bom_crlf_and_italic_tags():
    """AC-2: un SRT con BOM, saltos CRLF y etiquetas <i> se importa bien."""
    raw = (
        '﻿1\r\n00:00:01,000 --> 00:00:02,500\r\n<i>Hola</i> mundo\r\n\r\n2\r\n00:00:03,000 --> 00:00:04,000\r\nadiós\r\n'
    )

    cues = parse_srt(raw)

    assert _parsed_triples(cues) == [(1.0, 2.5, 'Hola mundo'), (3.0, 4.0, 'adiós')]


def test_parse_vtt_skips_the_header_and_the_cue_identifiers():
    """Un VTT con cabecera, identificadores de cue y punto en los tiempos se lee igual."""
    raw = 'WEBVTT\n\nintro\n00:00:00.500 --> 00:00:01.250\nBuenas tardes\n\n00:00:02.000 --> 00:00:03.000\nadiós\n'

    assert _parsed_triples(parse_vtt(raw)) == [(0.5, 1.25, 'Buenas tardes'), (2.0, 3.0, 'adiós')]


def test_imported_words_share_the_cue_time_by_characters():
    """Las palabras de un cue importado reparten su tiempo en proporción a sus caracteres."""
    cue = parse_srt('1\n00:00:00,000 --> 00:00:03,000\nab abcd\n')[0]

    # 6 caracteres en 3 s: «ab» (2 caracteres) toma 1 s y «abcd» (4) toma 2 s.
    assert [(w['text'], round(w['start'], 3), round(w['end'], 3)) for w in cue['words']] == [
        ('ab', 0.0, 1.0),
        ('abcd', 1.0, 3.0),
    ]
