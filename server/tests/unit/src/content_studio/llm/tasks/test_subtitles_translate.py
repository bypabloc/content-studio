"""Traducir subtítulos con el LLM, spec 021 AC-5."""

import json

from content_studio.llm.tasks import subtitles_translate
from content_studio.subtitles.document import load, new_document, save


def _cue(cue_id):
    return {
        'id': cue_id,
        'start': cue_id * 2.0,
        'end': cue_id * 2.0 + 1.5,
        'text': f'frase número {cue_id}',
        'words': [],
    }


def _doc(tmp_path, count=40):
    path = tmp_path / 'subtitles.json'
    doc = new_document(
        source_path='demo.mp4', kind='import', language='es', cues=[_cue(i) for i in range(1, count + 1)]
    )
    doc['style'] = {'max_chars': 42, 'max_lines': 2}
    save(doc, path)
    return path


class FakeModel:
    """Traduce cada cue a «frase N em português»; el cue 7 sale demasiado largo una o dos veces."""

    def __init__(self, long_times):
        self.long_times = long_times
        self.calls = []

    def __call__(self, messages, rule, check=None):
        payload = json.loads(messages[-1]['content'].split('CUES:')[1])
        self.calls.append([item['id'] for item in payload])
        answer = []
        for item in payload:
            text = f'frase {item["id"]} em português'
            if item['id'] == 7 and self.long_times > 0:
                text = 'uma frase muito comprida que não cabe de jeito nenhum em duas linhas de quarenta e dois'
                self.long_times -= 1
            answer.append({'id': item['id'], 'text': text})
        result = {'cues': answer}
        assert check is None or check(result) == []
        return result


def test_ac5_a_long_cue_is_retried_alone_and_the_track_has_every_id(tmp_path):
    """40 cues en dos lotes; el cue largo se reintenta solo y, si cabe, entra; la pista pt tiene todos los id."""
    path = _doc(tmp_path)
    model = FakeModel(long_times=1)

    result = subtitles_translate.run({'doc': str(path), 'language': 'pt'}, model)

    assert [len(call) for call in model.calls] == [30, 10, 1]
    assert model.calls[2] == [7]
    assert all(cue['flag'] is None for cue in result['cues'])
    doc = subtitles_translate.apply(load(path), result)
    assert [cue['id'] for cue in doc['tracks']['pt']] == list(range(1, 41))
    assert doc['tracks']['pt'][0] == {'id': 1, 'start': 2.0, 'end': 3.5, 'text': 'frase 1 em português'}


def test_ac5_a_cue_still_too_long_is_flagged(tmp_path):
    """Si después del reintento sigue largo, queda marcado para revisar."""
    path = _doc(tmp_path)

    result = subtitles_translate.run({'doc': str(path), 'language': 'pt'}, FakeModel(long_times=2))

    flagged = {cue['id']: cue['flag'] for cue in result['cues'] if cue['flag']}
    assert flagged == {7: 'too_long'}


def test_the_check_demands_every_id_of_the_batch():
    """Un lote al que le falta un id (o trae uno de más) no valida: el cliente reintenta."""
    check = subtitles_translate.ids_check([1, 2, 3])
    assert check({'cues': [{'id': 1, 'text': 'a'}, {'id': 2, 'text': 'b'}, {'id': 3, 'text': 'c'}]}) == []
    assert check({'cues': [{'id': 1, 'text': 'a'}, {'id': 3, 'text': 'c'}]})
    assert check(
        {'cues': [{'id': 1, 'text': 'a'}, {'id': 2, 'text': 'b'}, {'id': 3, 'text': 'c'}, {'id': 9, 'text': 'x'}]}
    )


def test_an_untranslated_cue_is_flagged(tmp_path):
    """Un cue idéntico al original (de más de dos palabras) queda marcado como sin traducir."""
    path = _doc(tmp_path, count=2)

    def same(messages, rule, check=None):
        payload = json.loads(messages[-1]['content'].split('CUES:')[1])
        return {'cues': [{'id': item['id'], 'text': item['text']} for item in payload]}

    result = subtitles_translate.run({'doc': str(path), 'language': 'pt'}, same)

    assert {cue['flag'] for cue in result['cues']} == {'untranslated'}


def test_validate_requires_a_known_language_and_the_project():
    """El idioma es de la lista y distinto del original; el proyecto debe existir."""
    assert subtitles_translate.validate({'doc': 'x.json', 'language': 'pt'}) == []
    assert subtitles_translate.validate({'doc': 'x.json', 'language': 'xx'})[0]['code'] == 'unknown_language'
    assert subtitles_translate.validate({'language': 'pt'})[0]['code'] == 'subtitle_project_not_found'
