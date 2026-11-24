"""Corregir la transcripción con un glosario, spec 021 AC-6."""

import json

from content_studio.llm.tasks import subtitles_correct
from content_studio.subtitles.document import load, new_document, save

CUE_1 = {
    'id': 1,
    'start': 0.0,
    'end': 1.6,
    'text': 'Hola desde Clinicae hoy',
    'words': [
        {'text': 'Hola', 'start': 0.0, 'end': 0.3},
        {'text': 'desde', 'start': 0.4, 'end': 0.7},
        {'text': 'Clinicae', 'start': 0.8, 'end': 1.2},
        {'text': 'hoy', 'start': 1.3, 'end': 1.6},
    ],
}
CUE_2 = {
    'id': 2,
    'start': 2.0,
    'end': 3.0,
    'text': 'todo bien',
    'words': [{'text': 'todo', 'start': 2.0, 'end': 2.4}, {'text': 'bien', 'start': 2.5, 'end': 3.0}],
}


def _doc(tmp_path):
    path = tmp_path / 'subtitles.json'
    save(new_document(source_path='demo.mp4', kind='cleaner', language='es', cues=[CUE_1, CUE_2]), path)
    return path


def test_ac6_a_glossary_fix_keeps_the_word_times_and_a_big_change_waits_for_review(tmp_path):
    """«Clinicae» → «Klinikae» conserva los tiempos; un cue con más de 2 palabras de diferencia queda para revisar."""
    path = _doc(tmp_path)
    sent = []

    def model(messages, rule, check=None):
        sent.append(messages[-1]['content'])
        return {
            'cues': [
                {'id': 1, 'text': 'Hola desde Klinikae hoy'},
                {'id': 2, 'text': 'todo está muy pero muy bien'},
            ]
        }

    result = subtitles_correct.run({'doc': str(path), 'glossary': ['Klinikae']}, model)

    assert 'Klinikae' in sent[0]
    first, second = result['cues']
    assert first['review'] is False
    assert [(w['text'], w['start'], w['end']) for w in first['words']] == [
        ('Hola', 0.0, 0.3),
        ('desde', 0.4, 0.7),
        ('Klinikae', 0.8, 1.2),
        ('hoy', 1.3, 1.6),
    ]
    assert second['review'] is True

    doc = subtitles_correct.apply(load(path), result)  # sin elegir: solo lo que no pide revisión
    assert doc['cues'][0]['text'] == 'Hola desde Klinikae hoy'
    assert doc['cues'][1]['text'] == 'todo bien'
    doc = subtitles_correct.apply(load(path), result, accepted=[2])
    assert doc['cues'][1]['text'] == 'todo está muy pero muy bien'
    assert doc['cues'][1]['end'] == 3.0


def test_unchanged_cues_are_not_proposed(tmp_path):
    """Un cue que vuelve igual no aparece en las sugerencias."""
    path = _doc(tmp_path)

    def model(messages, rule, check=None):
        payload = json.loads(messages[-1]['content'].split('CUES:')[1])
        return {'cues': [{'id': item['id'], 'text': item['text']} for item in payload]}

    assert subtitles_correct.run({'doc': str(path), 'glossary': []}, model) == {'cues': []}


def test_validate_checks_the_glossary():
    """El glosario es una lista corta de textos."""
    assert subtitles_correct.validate({'doc': 'x.json', 'glossary': ['Klinikae']}) == []
    assert subtitles_correct.validate({'doc': 'x.json', 'glossary': 'Klinikae'})[0]['code'] == 'invalid_glossary'
