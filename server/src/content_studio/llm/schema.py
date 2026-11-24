"""Validador mínimo de JSON schema (spec 021, D-3): solo los tipos y reglas que usan las tareas, sin jsonschema."""

from __future__ import annotations

import re
from typing import Any


def _type_error(value: object, kind: str) -> bool:
    if kind == 'object':
        return not isinstance(value, dict)
    if kind == 'array':
        return not isinstance(value, list)
    if kind == 'string':
        return not isinstance(value, str)
    if kind == 'boolean':
        return not isinstance(value, bool)
    if kind == 'integer':
        return isinstance(value, bool) or not isinstance(value, int)
    if kind == 'number':
        return isinstance(value, bool) or not isinstance(value, (int, float))
    return False


def validate(value: Any, rule: dict, path: str = '$') -> list[str]:
    """Los errores de `value` contra `rule`, cada uno con su ruta (`$.cues[3].text: longer than 84`).

    >>> validate({'n': 5}, {'type': 'object', 'properties': {'n': {'type': 'integer', 'maximum': 3}}})
    ['$.n: above 3']
    """
    kind = rule.get('type')
    if isinstance(kind, str) and _type_error(value, kind):
        return [f'{path}: expected {kind}']
    errors: list[str] = []
    if 'enum' in rule and value not in rule['enum']:
        errors.append(f'{path}: not one of {rule["enum"]}')
    if isinstance(value, str):
        if len(value) > rule.get('maxLength', len(value)):
            errors.append(f'{path}: longer than {rule["maxLength"]}')
        if len(value) < rule.get('minLength', 0):
            errors.append(f'{path}: shorter than {rule["minLength"]}')
        if 'pattern' in rule and not re.search(rule['pattern'], value):
            errors.append(f'{path}: does not match {rule["pattern"]}')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 'maximum' in rule and value > rule['maximum']:
            errors.append(f'{path}: above {rule["maximum"]}')
        if 'minimum' in rule and value < rule['minimum']:
            errors.append(f'{path}: below {rule["minimum"]}')
    if isinstance(value, list):
        if len(value) > rule.get('maxItems', len(value)):
            errors.append(f'{path}: more than {rule["maxItems"]} items')
        if len(value) < rule.get('minItems', 0):
            errors.append(f'{path}: fewer than {rule["minItems"]} items')
        for index, item in enumerate(value):
            errors += validate(item, rule.get('items', {}), f'{path}[{index}]')
    if isinstance(value, dict):
        properties = rule.get('properties', {})
        errors += [f'{path}.{name}: required' for name in rule.get('required', []) if name not in value]
        for name, item in value.items():
            if name in properties:
                errors += validate(item, properties[name], f'{path}.{name}')
            elif rule.get('additionalProperties') is False:
                errors.append(f'{path}.{name}: not allowed')
    return errors
