"""El proyecto de mezcla (spec 016, D-3): su documento, la caché de transcripciones y los tramos de voz."""

from __future__ import annotations

import json

from content_studio.mix import project


def test_new_document_starts_with_the_default_params_and_no_regions():
    """Un proyecto nuevo trae los parámetros por defecto y ninguna región hasta que se transcribe la voz."""
    doc = project.new_document('voz.wav', 'musica.wav', None, 'replace', 3)

    assert (doc['voice'], doc['music'], doc['video'], doc['video_mode'], doc['transcribe_job']) == (
        'voz.wav',
        'musica.wav',
        None,
        'replace',
        3,
    )
    assert doc['regions'] == []
    assert doc['params'] == project.DEFAULT_PARAMS


def test_editing_a_new_document_does_not_change_the_defaults():
    """Cada documento copia los parámetros: cambiar uno no toca los valores por defecto."""
    doc = project.new_document('a.wav', 'm.wav', None, 'replace', None)

    doc['params']['duck_db'] = -3.0

    assert project.DEFAULT_PARAMS['duck_db'] == -12.0


def test_transcript_key_is_the_cache_key_of_the_voice_file(tmp_path):
    """La clave de la caché son la ruta, el tamaño, la fecha, el modelo y el idioma automático de la voz."""
    voice = tmp_path / 'voz.wav'
    voice.write_bytes(b'abc')

    path, mtime, size, model, language = project.transcript_key(voice, 'large-v3-turbo')

    assert (path, size, model, language) == (str(voice), 3, 'large-v3-turbo', project.AUTO_LANGUAGE)
    assert mtime == voice.stat().st_mtime


def test_save_and_load_round_trip_the_document_with_accents(tmp_path):
    """El documento se guarda en UTF-8 y se lee igual, con nombres en español."""
    doc = project.new_document('Mañana, voz.wav', 'música.wav', None, 'replace', None)
    path = tmp_path / 'mix.json'

    project.save(path, doc)

    assert project.load(path) == doc


def test_speech_regions_joins_close_words_and_keeps_far_ones_apart(tmp_path):
    """Las palabras separadas por menos de `merge_gap` forman un tramo; una pausa larga, otro."""
    transcript = {
        'segments': [
            {'words': [{'start': 1.0, 'end': 1.5}, {'start': 1.6, 'end': 2.0}]},
            {'words': [{'start': 9.0, 'end': 9.5}]},
        ]
    }
    words = tmp_path / 'words.json'
    words.write_text(json.dumps(transcript), encoding='utf-8')

    regions = project.speech_regions(words, project.DEFAULT_PARAMS)

    assert len(regions) == 2
    assert all(isinstance(region, list) for region in regions)
    assert regions[0][0] < 1.0 and regions[0][1] > 2.0
    assert regions[1][0] < 9.0 < regions[1][1]
