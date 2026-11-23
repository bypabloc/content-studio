"""Interpolación de keyframes (spec 018, AC-1): las fixtures compartidas también las usa TypeScript."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.editor import keyframes

FIXTURES = Path(__file__).resolve().parents[4] / 'fixtures' / 'editor'
CASES = sorted(FIXTURES.glob('keyframes-*.json'))


@pytest.mark.parametrize('path', CASES, ids=lambda path: path.stem)
def test_value_at_matches_the_shared_fixture(path: Path) -> None:
    """AC-1: Python evalúa cada muestra de la fixture de keyframes compartida."""
    fixture = json.loads(path.read_text(encoding='utf-8'))

    for sample in fixture['samples']:
        assert keyframes.value_at(fixture['keyframes'], sample['t'], fixture['default']) == pytest.approx(
            sample['expected'], abs=1e-9
        )


@pytest.mark.parametrize('path', CASES, ids=lambda path: path.stem)
def test_segments_match_the_shared_fixture(path: Path) -> None:
    """AC-1: Python genera los mismos tramos que el espejo TypeScript."""
    fixture = json.loads(path.read_text(encoding='utf-8'))

    actual = keyframes.segments(fixture['keyframes'], fixture['clip_duration'])

    assert actual == [tuple(segment) for segment in fixture['segments']]
