"""Kit de grabación (spec 010, D-6 y AC-5): orden, duración, ppm y guion de cada estilo, como en docs/scripts/."""

from __future__ import annotations

from content_studio import paths
from content_studio.narration import recording_kit

REQUIRED = [
    'neutral', 'friendly', 'expert', 'clear', 'steady', 'soft',
    'energetic', 'dramatic', 'sad', 'intimate', 'neutral-en', 'neutral-end',
]  # fmt: skip


def test_the_twelve_required_styles_follow_the_guide_order():
    assert [item['style'] for item in recording_kit.kit() if not item['optional']] == REQUIRED


def test_every_required_take_lasts_between_8_and_12_seconds():
    for item in recording_kit.kit():
        if not item['optional']:
            low, high = item['duration']
            assert 8 <= low < high <= 12, item['style']


def test_ppm_comes_from_the_guide_and_whisper_has_none():
    by_style = {item['style']: item for item in recording_kit.kit()}

    assert by_style['expert']['ppm'] == 150
    assert by_style['energetic']['ppm'] == 175
    assert by_style['whisper']['ppm'] is None


def test_whisper_is_the_optional_style_at_the_end():
    items = recording_kit.kit()

    assert items[-1]['style'] == 'whisper' and items[-1]['optional'] is True


def test_each_style_points_to_its_script():
    assert recording_kit.script_file('expert').name == '03-experta.md'
    assert recording_kit.script_file('neutral-end').name == '00-neutral.md'


def test_plain_text_is_the_exact_text_of_the_versioned_transcript():
    for style in [*REQUIRED, 'whisper']:
        versioned = (paths.REFERENCE / 'default' / f'{style}.txt').read_text(encoding='utf-8').strip()
        assert recording_kit.plain_text(style) == versioned, style


def test_marked_text_keeps_the_notation_for_the_teleprompter():
    assert recording_kit.marked_text('expert').splitlines()[0] == '[directo] Mira, /'
