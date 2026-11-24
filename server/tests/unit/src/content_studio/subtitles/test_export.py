"""Exportar un documento a SRT, VTT o ASS (spec 014, D-3): el mismo texto que la quema y el ASS del client."""

from __future__ import annotations

import pytest

from content_studio.subtitles import export
from content_studio.subtitles.sources import from_cleaner

WORDS = [
    {'word': 'hola', 'start': 0.0, 'end': 0.4},
    {'word': 'mundo', 'start': 0.5, 'end': 0.9},
]


def test_render_writes_srt_and_vtt_with_the_cue_times():
    """SRT usa la coma en los milisegundos y VTT el punto y la cabecera WEBVTT."""
    document = from_cleaner(WORDS, source_path='clean.mp4', language='es')

    srt = export.render(document, 'srt')
    vtt = export.render(document, 'vtt')

    assert srt.startswith('1\n00:00:00,000 --> ')
    assert 'hola mundo' in srt
    assert vtt.startswith('WEBVTT')
    assert '00:00:00.000 --> ' in vtt


def test_render_writes_ass_with_the_document_style_over_the_classic_preset():
    """ASS trae el encabezado y un Dialogue; un estilo del documento cambia el de clásico."""
    document = from_cleaner(WORDS, source_path='clean.mp4', language='es')
    document['style'] = {'size': 90}

    ass = export.render(document, 'ass')

    assert '[Script Info]' in ass
    assert 'PlayResX: 1920' in ass
    assert ',90,' in ass
    assert 'Dialogue:' in ass


def test_render_refuses_an_unknown_format():
    """Un formato que no es srt, vtt ni ass es un ValueError con el nombre en el mensaje."""
    with pytest.raises(ValueError, match='mp3'):
        export.render(from_cleaner(WORDS, source_path='clean.mp4', language='es'), 'mp3')


def test_with_track_swaps_the_cues_for_the_translated_track_and_keeps_the_style():
    """Exportar una pista (spec 021): los cues pasan a ser los de `tracks[<idioma>]`; el estilo se queda."""
    document = from_cleaner(WORDS, source_path='clean.mp4', language='es')
    document['style'] = {'font': 'Geist'}
    document['tracks'] = {'pt': [{'id': 1, 'start': 0.0, 'end': 0.9, 'text': 'olá mundo'}]}

    translated = export.with_track(document, 'pt')

    assert [cue['text'] for cue in translated['cues']] == ['olá mundo']
    assert translated['language'] == 'pt' and translated['style'] == {'font': 'Geist'}
    assert 'olá mundo' in export.render(translated, 'srt')
    assert document['cues'][0]['text'] == 'hola mundo'


def test_with_track_rejects_a_language_without_a_track():
    """Una pista que el documento no tiene es un KeyError."""
    document = from_cleaner(WORDS, source_path='clean.mp4', language='es')

    with pytest.raises(KeyError):
        export.with_track(document, 'fr')
