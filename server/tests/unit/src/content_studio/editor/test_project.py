"""Modelo del proyecto del editor (spec 017, AC-1): validación, duración y migración del esquema v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.editor import project

FIXTURES = Path(__file__).resolve().parents[4] / 'fixtures' / 'editor'
INVALID = sorted(FIXTURES.glob('invalid-*.json'))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


@pytest.mark.parametrize('path', INVALID, ids=lambda p: p.stem)
def test_validate_rejects_the_invalid_fixtures_with_their_error_codes(path):
    """AC-1: `validate` devuelve exactamente los códigos de error de cada fixture inválida."""
    fixture = _load(path)

    codes = sorted(error['code'] for error in project.validate(fixture['doc']))

    assert codes == sorted(fixture['errors'])


def test_validate_accepts_the_document_of_a_valid_fixture():
    """AC-1: el documento de una fixture válida no tiene errores."""
    doc = _load(FIXTURES / 'ops-move-sin-pisar.json')['doc']

    assert project.validate(doc) == []


def test_duration_is_the_end_of_the_last_clip():
    """`duration` es el final del clip que más tarde termina; sin clips, 0."""
    doc = _load(FIXTURES / 'ops-delete-sin-ripple.json')['doc']

    assert project.duration(doc) == 12  # c3 empieza en 8 s y dura 4 s
    assert project.duration({**doc, 'clips': []}) == 0


def test_migrate_keeps_a_version_1_document_as_it_is():
    """El esquema v1 no cambia: `migrate` lo devuelve igual (la 018 sube de versión sin perder campos)."""
    doc = _load(FIXTURES / 'ops-split.json')['doc']

    assert project.migrate(doc) == doc
