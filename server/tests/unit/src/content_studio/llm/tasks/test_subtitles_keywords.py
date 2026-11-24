"""Sugerir palabras clave y emojis, spec 021 D-4."""

import pytest

from content_studio.llm.tasks import subtitles_keywords
from content_studio.subtitles.document import load, new_document, save


def _doc(tmp_path):
    words = [{'text': w, 'start': i * 0.5, 'end': i * 0.5 + 0.4} for i, w in enumerate(['Vende', 'más', 'rápido'])]
    cue = {'id': 1, 'start': 0.0, 'end': 1.4, 'text': 'Vende más rápido', 'words': words}
    path = tmp_path / 'subtitles.json'
    save(new_document(source_path='demo.mp4', kind='cleaner', language='es', cues=[cue]), path)
    return path


@pytest.mark.parametrize(
    ('emoji', 'single'),
    [('🚀', True), ('👍🏽', True), ('👩‍💻', True), ('🇨🇱', True), ('🚀🔥', False), ('ab', False), ('', False)],
)
def test_an_emoji_is_a_single_grapheme(emoji, single):
    """Un solo grafema: con tono de piel, secuencia ZWJ o bandera; dos emojis o letras no."""
    assert subtitles_keywords.single_grapheme(emoji) is single


def test_the_check_rejects_an_index_outside_the_cue(tmp_path):
    """El índice debe existir en el cue y el emoji ser uno solo."""
    check = subtitles_keywords.checker({1: 3})
    assert check({'cues': [{'id': 1, 'keyword_index': 2, 'emoji': '🚀'}]}) == []
    assert check({'cues': [{'id': 1, 'keyword_index': 5}]})
    assert check({'cues': [{'id': 1, 'keyword_index': 0, 'emoji': '🚀🔥'}]})


def test_suggestions_mark_the_keyword_when_applied(tmp_path):
    """La sugerencia nombra la palabra; al aplicarla, la palabra lleva su keyword con el emoji."""
    path = _doc(tmp_path)

    def model(messages, rule, check=None):
        answer = {'cues': [{'id': 1, 'keyword_index': 2, 'emoji': '🚀'}]}
        assert check(answer) == []
        return answer

    result = subtitles_keywords.run({'doc': str(path)}, model)

    assert result == {'cues': [{'id': 1, 'keyword_index': 2, 'word': 'rápido', 'emoji': '🚀'}]}
    doc = subtitles_keywords.apply(load(path), result)
    assert doc['cues'][0]['words'][2]['keyword'] == {'emoji': '🚀'}
    assert 'keyword' not in doc['cues'][0]['words'][0]
