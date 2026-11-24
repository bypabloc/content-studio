"""Velocidad de los clips (spec 019, AC-1/4): resultados de las fixtures compartidas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.editor import timing

FIXTURES = Path(__file__).resolve().parents[4] / 'fixtures' / 'editor'
CASES = [case for path in sorted(FIXTURES.glob('timing-*.json')) for case in json.loads(path.read_text())['cases']]


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['id'])
def test_ac4_speed_maps_duration_source_time_and_atempo_identically(case):
    """AC-1/4: las operaciones puras de velocidad coinciden con las fixtures compartidas."""
    clip = case['clip']

    assert timing.clip_duration(clip) == pytest.approx(case['duration'])
    assert timing.source_time(clip, case['timeline_time']) == pytest.approx(case['source_time'])
    assert timing.atempo_filters(clip['speed']) == case['atempo']


@pytest.mark.parametrize('speed', [0.249, 4.001, float('nan'), True])
def test_ac4_atempo_rejects_invalid_speed(speed):
    """AC-4: la cadena de filtros rechaza velocidades fuera del dominio v3."""
    with pytest.raises(ValueError, match='speed'):
        timing.atempo_filters(speed)
