"""Textos de la API y del CLI (spec 004, D-5; spec 007, D-1 y D-4): salen del catálogo con sus parámetros."""

from __future__ import annotations

from content_studio import messages


def test_t_fills_the_parameters_into_the_catalog_text():
    assert 'nope' in messages.t('error.unknown_engine', model='nope')


def test_t_returns_the_key_when_the_catalog_has_no_text():
    assert messages.t('codigo_sin_texto') == 'codigo_sin_texto'


def test_t_keeps_the_template_when_a_parameter_is_missing():
    assert '{model}' in messages.t('error.unknown_engine')
