"""Validador mínimo de JSON schema, spec 021 D-3."""

import pytest

from content_studio.llm import schema

ANSWER = {
    'type': 'object',
    'properties': {
        'caption': {'type': 'string', 'maxLength': 10},
        'bpm': {'type': 'integer', 'minimum': 30, 'maximum': 300},
        'signature': {'type': 'integer', 'enum': [2, 3, 4, 6]},
        'tags': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 2},
        'ok': {'type': 'boolean'},
        'score': {'type': 'number'},
    },
    'required': ['caption', 'bpm'],
    'additionalProperties': False,
}


def test_a_valid_answer_has_no_errors():
    """Un objeto que cumple cada regla no devuelve errores."""
    value = {'caption': 'piano', 'bpm': 90, 'signature': 4, 'tags': ['a'], 'ok': True, 'score': 0.5}
    assert schema.validate(value, ANSWER) == []


@pytest.mark.parametrize(
    ('value', 'error'),
    [
        ('text', '$: expected object'),
        ({'bpm': 90}, '$.caption: required'),
        ({'caption': 'x' * 11, 'bpm': 90}, '$.caption: longer than 10'),
        ({'caption': 'x', 'bpm': 400}, '$.bpm: above 300'),
        ({'caption': 'x', 'bpm': 10}, '$.bpm: below 30'),
        ({'caption': 'x', 'bpm': 9.5}, '$.bpm: expected integer'),
        ({'caption': 'x', 'bpm': True}, '$.bpm: expected integer'),
        ({'caption': 'x', 'bpm': 90, 'signature': 5}, '$.signature: not one of [2, 3, 4, 6]'),
        ({'caption': 'x', 'bpm': 90, 'tags': ['a', 'b', 'c']}, '$.tags: more than 2 items'),
        ({'caption': 'x', 'bpm': 90, 'tags': [1]}, '$.tags[0]: expected string'),
        ({'caption': 'x', 'bpm': 90, 'extra': 1}, '$.extra: not allowed'),
        ({'caption': 'x', 'bpm': 90, 'ok': 'yes'}, '$.ok: expected boolean'),
        ({'caption': 'x', 'bpm': 90, 'score': 'high'}, '$.score: expected number'),
    ],
)
def test_each_rule_reports_its_path(value, error):
    """Cada error dice la ruta y la regla, para devolvérselo al modelo en el reintento."""
    assert error in schema.validate(value, ANSWER)


def test_min_items_and_min_length():
    """minItems y minLength también se respetan."""
    rule = {'type': 'array', 'minItems': 1, 'items': {'type': 'string', 'minLength': 1}}
    assert schema.validate([], rule) == ['$: fewer than 1 items']
    assert schema.validate([''], rule) == ['$[0]: shorter than 1']


def test_pattern():
    """pattern (los capítulos en `m:ss`, spec 021): un texto que no lo cumple es un error con su ruta."""
    rule = {'type': 'string', 'pattern': '^[0-9]+:[0-5][0-9]$'}
    assert schema.validate('1:39', rule) == []
    assert schema.validate('0.51', rule) == ['$: does not match ^[0-9]+:[0-5][0-9]$']
