"""Validacion del esquema v3 del Editor, separada del ciclo de migracion."""

from __future__ import annotations

import pytest

from content_studio.editor import schema

VALID_TEXT = {
    'content': 'Hola',
    'font': 'Inter',
    'weight': 700,
    'size': 48,
    'color': '#ffffff',
    'stroke': {'width': 2, 'color': '#000000'},
    'shadow': {'x': 1, 'y': 2, 'blur': 3, 'color': '#00000080'},
    'align': 'center',
    'line_height': 1.2,
    'max_width': 800,
}


@pytest.mark.parametrize('speed', [0.25, 0.5, 1, 2, 4])
def test_speed_accepts_the_v3_range(speed):
    assert schema.valid_speed(speed)


@pytest.mark.parametrize('speed', [0.249, 4.001, float('nan'), True, '2'])
def test_speed_rejects_invalid_values(speed):
    assert not schema.valid_speed(speed)


def test_track_error_accepts_audio_video_and_subtitle_references():
    assert schema.track_error({'id': 'a', 'kind': 'audio'}) is None
    assert schema.track_error({'id': 'v', 'kind': 'video'}) is None
    assert schema.track_error({'id': 's', 'kind': 'subtitles', 'subtitles_project': 'project-1'}) is None


def test_track_error_rejects_unknown_kind_and_missing_subtitle_project():
    assert schema.track_error({'id': 'x', 'kind': 'other'}) == 'bad_track_kind'
    assert schema.track_error({'id': 's', 'kind': 'subtitles'}) == 'bad_subtitles_track'


def test_color_and_blend_mode_validation():
    color = {'brightness': 0, 'contrast': 1, 'saturation': 1, 'gamma': 1, 'lut': 'media/luts/id.cube'}
    assert schema.valid_color(color)
    assert schema.valid_blend_mode('multiply')
    assert not schema.valid_color({**color, 'gamma': 10.1})
    assert not schema.valid_color({**color, 'lut': 3})
    assert not schema.valid_blend_mode('invalid')


def test_chroma_validation_checks_color_and_thresholds():
    assert schema.valid_chroma({'color': '#00ff00', 'similarity': 0.3, 'blend': 0.1})
    assert not schema.valid_chroma({'color': 'green', 'similarity': 0.3, 'blend': 0.1})
    assert not schema.valid_chroma({'color': '#00ff00', 'similarity': 1.1, 'blend': 0.1})


def test_text_validation_accepts_style_and_rejects_unsafe_or_incomplete_values():
    assert schema.valid_text(VALID_TEXT, 'media/text-title-a1.png')
    assert not schema.valid_text(VALID_TEXT, '../media/text-title-a1.png')
    assert not schema.valid_text({**VALID_TEXT, 'size': 0}, 'media/text-title-a1.png')
    assert not schema.valid_text({**VALID_TEXT, 'stroke': {}}, 'media/text-title-a1.png')
    assert not schema.valid_text({**VALID_TEXT, 'shadow': {}}, 'media/text-title-a1.png')
    assert not schema.valid_text(
        {**VALID_TEXT, 'box': {'color': '#000', 'padding': -1, 'radius': 0}}, 'media/text-title-a1.png'
    )
