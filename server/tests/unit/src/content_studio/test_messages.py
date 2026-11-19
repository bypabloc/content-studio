"""Textos de error de la API (spec 004, D-5): salen de messages/es.json y se llenan con los parámetros."""

from __future__ import annotations

from content_studio import messages


def test_t_fills_the_parameters_into_the_catalog_text():
    assert 'nope' in messages.t('unknown_engine', model='nope')


def test_t_returns_the_code_when_the_catalog_has_no_text():
    assert messages.t('codigo_sin_texto') == 'codigo_sin_texto'


def test_t_keeps_the_template_when_a_parameter_is_missing():
    assert '{model}' in messages.t('unknown_engine')
