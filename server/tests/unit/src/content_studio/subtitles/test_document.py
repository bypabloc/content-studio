"""Documento de subtítulos (spec 014, D-1, AC-5): operaciones puras sobre cues y palabras, y guardado en disco."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.subtitles.document import load, merge, new_document, save, set_text, shift, split


def _cue(cue_id: int, words: list[tuple[str, float, float]]) -> dict:
    return {
        'id': cue_id,
        'start': words[0][1],
        'end': words[-1][2],
        'text': ' '.join(word for word, _, _ in words),
        'words': [{'start': start, 'end': end, 'text': word} for word, start, end in words],
    }


def _doc() -> dict:
    cues = [
        _cue(1, [('hola', 0.0, 0.4), ('mundo', 0.5, 0.9), ('buenas', 1.0, 1.4), ('tardes', 1.5, 1.9)]),
        _cue(2, [('a', 2.0, 2.1), ('todos', 2.2, 2.6)]),
    ]
    return new_document(source_path='entrada.wav', kind='file', language='es', cues=cues)


def test_ac5_split_and_merge_return_the_original_document():
    """AC-5: dividir un cue en la palabra 3 y unirlo otra vez deja el documento igual que al principio."""
    original = _doc()

    divided = split(original, cue_id=1, at_word=3)
    assert [cue['text'] for cue in divided['cues']] == ['hola mundo buenas', 'tardes', 'a todos']

    assert merge(divided, first_id=1, second_id=3) == original


def test_ac5_set_text_with_one_more_word_spreads_the_times_inside_the_cue_without_overlap():
    """AC-5: con una palabra más, los tiempos se reparten dentro del intervalo del cue y no pisan al siguiente."""
    original = _doc()

    edited = set_text(original, cue_id=1, text='hola a todos mundo buenas tardes')

    cue = next(c for c in edited['cues'] if c['id'] == 1)
    assert (cue['start'], cue['end']) == (0.0, 1.9)
    assert cue['text'] == 'hola a todos mundo buenas tardes'
    times = [(word['start'], word['end']) for word in cue['words']]
    assert times[0][0] == 0.0
    assert times[-1][1] == 1.9
    for (_, end), (next_start, _) in zip(times, times[1:], strict=False):
        assert end <= next_start + 1e-9
    next_cue = next(c for c in edited['cues'] if c['id'] == 2)
    assert cue['end'] <= next_cue['start']
    assert original == _doc()  # el documento de entrada no cambia


def test_shift_moves_the_cue_and_its_words_by_the_same_delta():
    """Desplazar un cue mueve su inicio, su fin y los tiempos de sus palabras."""
    cue = next(c for c in shift(_doc(), cue_id=2, delta=0.5)['cues'] if c['id'] == 2)

    assert (cue['start'], cue['end']) == (2.5, 3.1)
    assert cue['words'][0]['start'] == 2.5
    assert cue['words'][-1]['end'] == 3.1


def test_split_rejects_a_word_index_outside_the_cue():
    """Dividir en la primera palabra o después de la última no deja dos cues: es un error."""
    with pytest.raises(ValueError):
        split(_doc(), cue_id=1, at_word=0)
    with pytest.raises(ValueError):
        split(_doc(), cue_id=1, at_word=4)


def test_save_and_load_keep_the_document_and_its_version(tmp_path: Path):
    """El documento se guarda como JSON en UTF-8 con su versión y se lee igual."""
    path = tmp_path / 'subtitles.json'

    save(_doc(), path)

    assert load(path) == _doc()
    assert json.loads(path.read_text(encoding='utf-8'))['version'] == 1
