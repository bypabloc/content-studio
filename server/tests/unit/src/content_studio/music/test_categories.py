"""Categorías de los presets (spec 011, D-2, AC-4): todo preset tiene una categoría válida."""

from __future__ import annotations

from content_studio.music.categories import CATEGORIES, category_of
from content_studio.music.styles import STYLES


def test_every_preset_has_a_known_category():
    assert all(style['category'] in CATEGORIES for style in STYLES.values())
    assert len(STYLES) == 126


def test_the_family_of_a_preset_comes_from_its_name():
    assert category_of('lofi-jazz') == 'lofi'
    assert category_of('ad-fintech') == 'ads'
    assert category_of('demo-saas') == 'demo'
    assert category_of('piano-pop') == 'acoustic'


def test_the_exceptions_go_where_their_sound_goes():
    assert category_of('deep-focus') == 'ambient'
    assert category_of('deep-house') == 'electronic'
    assert category_of('tropical-house') == 'electronic'
    assert category_of('workout') == 'electronic'


def test_a_name_without_a_family_is_a_genre():
    assert category_of('something-new') == 'genres'
