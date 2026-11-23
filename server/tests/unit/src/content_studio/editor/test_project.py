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


def test_validate_accepts_a_visual_project_with_keyframes_transition_and_link():
    """AC-1: una pista visual, su transición y el audio enlazado son válidos en v2."""
    doc = _load(FIXTURES / 'valid-visual-v2.json')['doc']

    assert project.validate(doc) == []


def test_duration_is_the_end_of_the_last_clip():
    """`duration` es el final del clip que más tarde termina; sin clips, 0."""
    doc = _load(FIXTURES / 'ops-delete-sin-ripple.json')['doc']

    assert project.duration(doc) == 12  # c3 empieza en 8 s y dura 4 s
    assert project.duration({**doc, 'clips': []}) == 0


def test_migrate_preserves_v1_fields_and_adds_v3_defaults():
    """AC-1: la migración suma lienzo y transiciones sin mutar ni perder campos v1."""
    doc = _load(FIXTURES / 'ops-split.json')['doc']
    before = json.loads(json.dumps(doc))

    migrated = project.migrate(doc)

    expected = json.loads(json.dumps(before))
    expected.update(version=3, canvas=project.DEFAULT_CANVAS, transitions=[])
    for track in expected['tracks']:
        track.setdefault('kind', 'audio')
    for clip in expected['clips']:
        clip['speed'] = 1
    assert migrated == expected
    assert doc == before
    assert project.validate(migrated) == []


def test_migrate_v2_to_v3_adds_effect_defaults_without_losing_fields():
    """AC-1: la migracion v2 a v3 conserva los campos y completa los valores por defecto."""
    doc = _load(FIXTURES / 'valid-visual-v2.json')['doc']
    before = json.loads(json.dumps(doc))

    migrated = project.migrate(doc)

    expected = json.loads(json.dumps(before))
    expected['version'] = 3
    for clip in expected['clips']:
        clip['speed'] = 1
        if 'media' in clip:
            clip['color'] = {'brightness': 0, 'contrast': 1, 'saturation': 1, 'gamma': 1}
            clip['blend_mode'] = 'normal'
    assert migrated == expected
    assert doc == before
    assert project.validate(migrated) == []


def test_migrate_v1_to_v3_applies_both_schema_steps():
    """AC-1: el proyecto v1 mantiene lienzo, tipo de pista y velocidad por defecto en v3."""
    doc = _load(FIXTURES / 'ops-split.json')['doc']

    migrated = project.migrate(doc)

    assert migrated['version'] == 3
    assert migrated['canvas'] == project.DEFAULT_CANVAS
    assert migrated['tracks'][0]['kind'] == 'audio'
    assert all(clip['speed'] == 1 for clip in migrated['clips'])


def test_validate_rejects_v3_speed_outside_the_supported_range():
    """AC-1: el proyecto v3 solo acepta velocidades de 0.25x a 4x."""
    doc = project.migrate(_load(FIXTURES / 'valid-visual-v2.json')['doc'])
    doc['clips'][0]['speed'] = 4.01

    assert project.validate(doc) == [{'code': 'bad_speed', 'id': doc['clips'][0]['id']}]
