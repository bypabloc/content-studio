"""Textos de la API y del CLI (spec 004, D-5; spec 007, D-1 y D-4): salen del catálogo con sus parámetros."""

from __future__ import annotations

from content_studio import messages
from content_studio.music.engines.registry import MODELS as MUSIC_MODELS
from content_studio.music.styles import STYLES as MUSIC_STYLES
from content_studio.narration.engines.registry import ENGINES as NARRATION_ENGINES
from content_studio.narration.parser import STYLES as NARRATION_STYLES


def test_t_fills_the_parameters_into_the_catalog_text():
    assert 'nope' in messages.t('error.unknown_engine', model='nope')


def test_t_returns_the_key_when_the_catalog_has_no_text():
    assert messages.t('codigo_sin_texto') == 'codigo_sin_texto'


def test_t_keeps_the_template_when_a_parameter_is_missing():
    assert '{model}' in messages.t('error.unknown_engine')


def test_t_reads_the_catalog_of_the_locale_it_is_given():
    assert 'nope' in messages.t('error.unknown_engine', 'en', model='nope')
    assert 'nope' in messages.t('error.unknown_engine', 'pt', model='nope')
    assert messages.t('error.unknown_engine', 'en', model='x') != messages.t('error.unknown_engine', 'es', model='x')


def test_t_falls_back_to_spanish_for_a_locale_without_catalog():
    assert messages.t('error.unknown_engine', 'fr', model='x') == messages.t('error.unknown_engine', 'es', model='x')


def test_ac3_every_registry_id_has_a_label():
    """Cada estilo, motor y modelo de los registros tiene su `label.*` en el catálogo (spec 007, AC-3 y D-7)."""
    keys = [
        *(f'label.narration.style.{name}' for name in NARRATION_STYLES),
        *(f'label.narration.engine.{name}' for name in NARRATION_ENGINES),
        *(f'label.music.style.{name}' for name in MUSIC_STYLES),
        *(f'label.music.model.{name}' for name in MUSIC_MODELS),
    ]
    assert [key for key in keys if messages.t(key) == key] == []
