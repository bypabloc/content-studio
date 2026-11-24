"""Describir la música en español para ACE-Step, spec 021 AC-7."""

import pytest

from content_studio.llm import schema
from content_studio.llm.tasks import music_caption


def _answer(**changes):
    answer = {'caption': 'soft piano, rain ambience, calm, cooking tutorial', 'key': 'C Major', 'bpm': 80}
    return {**answer, 'time_signature': '4', **changes}


def test_ac7_an_unknown_key_or_bpm_fails_the_schema_so_the_client_retries():
    """«H Major» y 400 BPM no cumplen el schema: el cliente reintenta con el error."""
    assert schema.validate(_answer(key='H Major'), music_caption.SCHEMA)
    assert schema.validate(_answer(bpm=400), music_caption.SCHEMA)
    assert schema.validate(_answer(time_signature='5'), music_caption.SCHEMA)
    assert schema.validate(_answer(), music_caption.SCHEMA) == []


@pytest.mark.parametrize(
    'caption',
    ['soft piano, 80 bpm, calm', 'soft piano in C major, calm', 'piano suave, lluvia, cocina tranquila'],
)
def test_ac7_tempo_key_or_spanish_in_the_caption_fail_the_check(caption):
    """El caption no lleva tempo ni tonalidad (van aparte) y está en inglés."""
    assert music_caption.check(_answer(caption=caption))


def test_ac7_no_vocals_is_appended_when_missing():
    """Un caption sin «no vocals» se completa; uno que ya lo tiene queda igual."""
    seen = []

    def ask(messages, rule, check=None):
        seen.append((rule, check))
        return _answer()

    result = music_caption.run({'description': 'algo tranquilo con piano y lluvia'}, ask)

    assert result['caption'] == 'soft piano, rain ambience, calm, cooking tutorial, no vocals'
    assert (result['key'], result['bpm'], result['time_signature']) == ('C Major', 80, '4')
    assert seen[0] == (music_caption.SCHEMA, music_caption.check)
    already = music_caption.run({'description': 'x'}, lambda *a, **k: _answer(caption='piano, no vocals'))
    assert already['caption'] == 'piano, no vocals'


def test_the_ace_step_guide_comes_from_the_catalog():
    """Las recomendaciones de ACE-Step se toman de styles.py: instrumentos concretos y «no vocals» al final."""
    assert 'no vocals' in music_caption.GUIDE
    assert 'ACE-Step' in music_caption.GUIDE


def test_the_keys_are_the_stable_ones_of_the_catalog():
    """Las tonalidades válidas son las del catálogo de la 011."""
    from content_studio.music.styles import STYLES

    assert set(music_caption.KEYS) == {style['key'] for style in STYLES.values()}


def test_validate_requires_a_description():
    """La descripción es obligatoria y corta."""
    assert music_caption.validate({'description': ''})[0]['code'] == 'invalid_text'
    assert music_caption.validate({'description': 'x' * 1001})[0]['code'] == 'invalid_text'
    assert music_caption.validate({'description': 'piano'}) == []
