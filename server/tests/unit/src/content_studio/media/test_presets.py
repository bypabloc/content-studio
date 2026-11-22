"""Presets de redes (spec 015, D-2, T3): el ★ del recomendado sale de la proporción de la fuente, y cada preset trae su
tamaño, sus fps y su encuadre por defecto."""

from __future__ import annotations

import pytest

from content_studio.media import presets


@pytest.mark.parametrize(
    ('aspect', 'recommended'),
    [
        (9 / 16, 'reels'),  # vertical
        (1.0, 'square'),  # cuadrado
        (16 / 9, 'youtube-1080'),  # horizontal
    ],
)
def test_the_star_follows_the_aspect_of_the_source(aspect, recommended):
    """El recomendado es el preset de la proporción de la fuente: vertical → Reels, cuadrado → cuadrado, horizontal →
    YouTube 1080."""
    assert presets.recommended(aspect) == recommended


def test_reels_is_1080_by_1920_at_30_fps_with_the_center_reframe():
    """Reels: 1080×1920 a 30 fps, con encuadre centrado por defecto."""
    reels = presets.PRESETS['reels']

    assert (reels['width'], reels['height'], reels['fps']) == (1080, 1920, 30)
    assert reels['reframe'] == 'center'


def test_shorts_allows_up_to_60_fps_and_youtube_4k_is_2160p():
    """Shorts admite hasta 60 fps; YouTube 4K es 3840×2160."""
    assert presets.PRESETS['shorts']['fps'] == 60
    assert (presets.PRESETS['youtube-4k']['width'], presets.PRESETS['youtube-4k']['height']) == (3840, 2160)


def test_every_preset_has_a_size_and_a_reframe_mode():
    """Todos los presets traen tamaño, fps y un encuadre por defecto válido."""
    for name, preset in presets.PRESETS.items():
        assert preset['width'] > 0 and preset['height'] > 0, name
        assert preset['fps'] > 0, name
        assert preset['reframe'] in {'center'}, name
