"""Textos de la API y del CLI (spec 004, D-5; spec 007, D-1 y D-4): salen del catálogo con sus parámetros."""

from __future__ import annotations

from content_studio import messages


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
