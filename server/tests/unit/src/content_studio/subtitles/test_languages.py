"""Idiomas de traducción de subtítulos, spec 021 D-4."""

from content_studio.subtitles import languages


def test_english_is_recommended_and_the_list_has_the_common_ones():
    """El inglés lleva ★; la lista trae es, en, pt, fr, it y de con su nombre propio."""
    codes = [item['code'] for item in languages.status()]
    assert {'es', 'en', 'pt', 'fr', 'it', 'de'} <= set(codes)
    assert languages.RECOMMENDED == 'en'
    assert next(item for item in languages.status() if item['code'] == 'pt')['name'] == 'Português'
    assert [item['code'] for item in languages.status() if item['recommended']] == ['en']
