"""Estilos y presets de subtítulos (spec 014, D-5): copias independientes, los cuatro presets y el color de ASS."""

from __future__ import annotations

import pytest

from content_studio.subtitles import styles


def test_preset_returns_a_copy_so_changing_it_does_not_change_the_stored_preset():
    """`preset()` devuelve una copia: cambiarla no altera el preset guardado."""
    copied = styles.preset('reels')
    copied['size'] = 10

    assert styles.PRESETS['reels']['size'] == 72
    assert styles.preset('reels')['size'] == 72


def test_the_four_built_in_presets_have_their_modes():
    """Los cuatro presets de la spec: clásico, redes (con pop y dos palabras), karaoke y mínimo."""
    assert set(styles.PRESETS) == {'classic', 'reels', 'karaoke', 'minimal'}
    assert styles.PRESETS['reels']['mode'] == 'social'
    assert styles.PRESETS['reels']['words_per_cue'] == 2
    assert styles.PRESETS['karaoke']['mode'] == 'karaoke'
    assert styles.PRESETS['minimal']['back_box'] == '#00000080'


def test_an_unknown_preset_is_an_error_that_names_it():
    """Un nombre de preset que no existe es un ValueError con el nombre en el mensaje."""
    with pytest.raises(ValueError, match='nope'):
        styles.preset('nope')


def test_ass_color_converts_rgb_and_alpha_to_the_ass_bgr_form():
    """`#RRGGBB` va a `&HBBGGRR&`; con alfa, la opacidad va invertida en el byte de alfa de ASS."""
    assert styles.ass_color('#FFD400') == '&H00D4FF&'
    assert styles.ass_color('#00000080') == '&H7F000000&'
    assert styles.ass_color('#ffffff') == '&HFFFFFF&'


def test_alignment_maps_the_three_vertical_positions():
    """bottom, middle y top son las posiciones 2, 5 y 8 del teclado numérico de ASS."""
    assert styles.ALIGNMENT == {'bottom': 2, 'middle': 5, 'top': 8}
