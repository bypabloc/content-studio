"""Errores con código de la API (spec 004, D-5): guardan código, parámetros y campos extra."""

from __future__ import annotations

from content_studio.api.errors import ApiError


def test_api_error_keeps_its_code_params_and_extra_fields():
    error = ApiError(422, 'unknown_engine', extra={'errors': [1]}, model='nope')

    assert (error.status_code, error.code, error.params, error.extra) == (
        422,
        'unknown_engine',
        {'model': 'nope'},
        {'errors': [1]},
    )


def test_api_error_without_extra_has_an_empty_extra():
    assert ApiError(404, 'not_found').extra == {}
