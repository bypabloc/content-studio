"""Segmentación de subtítulos (spec 014, D-2, AC-1): función pura sobre palabras con tiempos."""

from __future__ import annotations

from content_studio.subtitles.segment import segment, wrap_lines

# 30 palabras: frases que terminan en punto y comas en medio.
TEXT = (
    'Hoy vamos a ver cómo se hace, paso a paso, un video corto. Primero preparamos la idea y el guion; luego '
    'grabamos la voz con calma. Revisamos los cortes, listo.'
)


def _words(text: str) -> list[dict]:
    """Palabras con tiempos regulares: 0,4 s de voz y 0,1 s de pausa."""
    return [
        {'word': word, 'start': round(i * 0.5, 3), 'end': round(i * 0.5 + 0.4, 3)}
        for i, word in enumerate(text.split())
    ]


def test_wrap_lines_never_splits_a_word_and_keeps_each_line_within_the_limit():
    """Las palabras se reparten en renglones sin cortar ninguna y ninguno pasa del límite."""
    assert wrap_lines(['uno', 'dos', 'tres', 'cuatro'], 8) == ['uno dos', 'tres', 'cuatro']


def test_ac1_no_cue_passes_two_lines_of_42_characters_or_seven_seconds():
    """AC-1: ningún cue pasa de 2 líneas de 42 caracteres ni de 7 s, y su texto es la unión de sus palabras."""
    cues = segment(_words(TEXT), max_chars=42, max_lines=2, max_duration=7.0)

    assert len(TEXT.split()) == 30
    for cue in cues:
        lines = wrap_lines([w['word'] for w in cue['words']], 42)
        assert len(lines) <= 2
        assert all(len(line) <= 42 for line in lines)
        assert cue['end'] - cue['start'] <= 7.0 + 1e-9
        assert cue['text'] == ' '.join(w['word'] for w in cue['words'])


def test_ac1_cues_start_after_every_strong_punctuation_mark():
    """AC-1: cada palabra que termina en . ? o ! cierra un cue: el siguiente empieza justo después."""
    words = _words(TEXT)
    cues = segment(words, max_chars=42, max_lines=2, max_duration=7.0)
    starts = {cue['start'] for cue in cues}

    for index, word in enumerate(words[:-1]):
        if word['word'][-1] in '.?!':
            assert words[index + 1]['start'] in starts


def test_ac1_words_per_cue_gives_one_or_two_words_and_never_crosses_strong_punctuation():
    """AC-1: con words_per_cue 2, cada cue tiene 1 o 2 palabras, todas las palabras quedan y ninguno cruza un punto."""
    cues = segment(_words(TEXT), words_per_cue=2)

    assert all(1 <= len(cue['words']) <= 2 for cue in cues)
    assert sum(len(cue['words']) for cue in cues) == 30
    for cue in cues:
        assert all(word['word'][-1] not in '.?!' for word in cue['words'][:-1])
