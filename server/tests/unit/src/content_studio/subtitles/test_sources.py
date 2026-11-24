"""Orígenes de subtítulos (spec 014, D-4, AC-4): alineación del guion con las palabras de whisper y los demás orígenes.

La transcripción va simulada: las palabras llegan ya hechas, como las devuelve faster-whisper.
"""

from __future__ import annotations

from content_studio.subtitles.sources import align, from_cleaner, from_import, from_narration, from_words

# cspell:ignore ahora: palabra del guion de la prueba de interpolación.


def _w(text: str, start: float, end: float) -> dict:
    return {'word': text, 'start': start, 'end': end}


# Lo que whisper oyó: «una» quedó partida en «un a».
WHISPER = [
    _w('hola', 0.0, 0.4),
    _w('mundo', 0.5, 0.9),
    _w('esto', 1.0, 1.3),
    _w('es', 1.4, 1.6),
    _w('un', 1.7, 1.9),
    _w('a', 2.0, 2.1),
    _w('prueba', 2.2, 2.7),
]


def test_ac4_align_narration_keeps_the_script_text_and_times_every_word():
    """AC-4: el texto es el del guion y cada palabra tiene tiempo, también «una», que whisper partió en «un a»."""
    aligned = align('Hola mundo, esto es una prueba', WHISPER)

    assert [w['word'] for w in aligned] == ['Hola', 'mundo,', 'esto', 'es', 'una', 'prueba']
    assert all(w['end'] > w['start'] for w in aligned)
    assert [w['start'] for w in aligned] == sorted(w['start'] for w in aligned)
    assert (aligned[4]['start'], aligned[4]['end']) == (1.7, 2.1)  # «una» toma el tramo de «un a»
    assert (aligned[5]['start'], aligned[5]['end']) == (2.2, 2.7)


def test_align_interpolates_a_script_word_that_whisper_did_not_hear():
    """Una palabra del guion sin par en whisper se interpola entre sus vecinas con tiempo."""
    aligned = align('Hola mundo ahora esto es una prueba', WHISPER)

    ahora = next(w for w in aligned if w['word'] == 'ahora')
    assert 0.9 <= ahora['start'] < ahora['end'] <= 1.0


def test_align_ignores_accents_case_and_punctuation():
    """La comparación no distingue tildes, mayúsculas ni signos: «Está» y «esta» son la misma palabra."""
    aligned = align('¡Está lista!', [_w('esta', 0.0, 0.5), _w('lista', 0.6, 1.0)])

    assert [w['word'] for w in aligned] == ['¡Está', 'lista!']
    assert (aligned[0]['start'], aligned[0]['end']) == (0.0, 0.5)


def test_from_words_builds_cues_with_ids_and_text_words():
    """Un documento con cues numerados y palabras con `text`, a partir de palabras con tiempos."""
    doc = from_words(WHISPER, source_path='entrada.wav', kind='file', language='es')

    assert doc['source'] == {'path': 'entrada.wav', 'kind': 'file'}
    assert [cue['id'] for cue in doc['cues']] == list(range(1, len(doc['cues']) + 1))
    assert all('text' in word and 'word' not in word for cue in doc['cues'] for word in cue['words'])
    assert ' '.join(cue['text'] for cue in doc['cues']) == 'hola mundo esto es un a prueba'


def test_from_cleaner_takes_the_cleaner_words_without_transcribing():
    """El origen del limpiador usa sus palabras (ya en el tiempo del limpio) y su kind es «cleaner»."""
    doc = from_cleaner(WHISPER, source_path='clean.mp4', language='es')

    assert doc['source']['kind'] == 'cleaner'
    assert doc['cues'][0]['words'][0] == {'text': 'hola', 'start': 0.0, 'end': 0.4}


def test_from_narration_aligns_the_script_before_segmenting():
    """El origen de narración alinea el guion con whisper: el texto de los cues es el del guion."""
    doc = from_narration('Hola mundo, esto es una prueba', WHISPER, source_path='nota.wav', language='es')

    assert doc['source']['kind'] == 'narration'
    assert ' '.join(cue['text'] for cue in doc['cues']) == 'Hola mundo, esto es una prueba'


def test_from_import_reads_an_srt_or_a_vtt_by_its_header():
    """Un SRT o un VTT importado queda como documento, sin GPU."""
    srt = '1\n00:00:00,000 --> 00:00:01,000\nHola\n'
    vtt = 'WEBVTT\n\n00:00:02.000 --> 00:00:03.000\nadiós\n'

    assert [cue['text'] for cue in from_import(srt, source_path='a.srt', language='es')['cues']] == ['Hola']
    assert [cue['text'] for cue in from_import(vtt, source_path='b.vtt', language='es')['cues']] == ['adiós']


def test_from_words_strips_the_leading_space_that_faster_whisper_puts_on_each_word():
    """faster-whisper da « hola»: el cue no queda con dobles espacios y las palabras quedan sin espacios (spec 021)."""
    doc = from_words([_w(' hola', 0.0, 0.4), _w(' mundo', 0.5, 0.9)], source_path='a.mp4', kind='file', language='es')

    assert doc['cues'][0]['text'] == 'hola mundo'
    assert [word['text'] for word in doc['cues'][0]['words']] == ['hola', 'mundo']
