"""Operaciones puras del editor (spec 017, AC-1): cada fixture `ops-*.json` da el resultado que dice `expected`."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from content_studio.editor import ops

FIXTURES = Path(__file__).resolve().parents[4] / 'fixtures' / 'editor'
OPS = sorted(FIXTURES.glob('ops-*.json'))


@pytest.mark.parametrize('path', OPS, ids=lambda p: p.stem)
def test_the_operation_gives_the_expected_clips(path):
    """AC-1: aplicar la operación de la fixture da los ids y los campos de `expected`, y no toca la entrada."""
    fixture = json.loads(path.read_text(encoding='utf-8'))
    before = copy.deepcopy(fixture['doc'])

    result = ops.apply(fixture['doc'], fixture['op'])

    expected = fixture['expected']
    assert sorted(clip['id'] for clip in result['clips']) == sorted(expected['ids'])
    by_id = {clip['id']: clip for clip in result['clips']}
    for clip_id, fields in expected['clips'].items():
        assert {key: by_id[clip_id][key] for key in fields} == fields
    tracks = {track['id']: track for track in result['tracks']}
    for track_id, fields in expected.get('tracks', {}).items():
        assert {key: tracks[track_id][key] for key in fields} == fields
    if 'track_ids' in expected:
        assert [track['id'] for track in result['tracks']] == expected['track_ids']
    if 'markers' in expected:
        assert result['markers'] == expected['markers']
    assert fixture['doc'] == before


def test_apply_rejects_an_unknown_operation():
    """Una operación que no existe falla con su código, no con un error genérico."""
    doc = {'version': 1, 'name': 'x', 'sample_rate': 48000, 'tracks': [], 'clips': [], 'markers': []}

    with pytest.raises(ops.OpError) as caught:
        ops.apply(doc, {'type': 'nope'})

    assert caught.value.code == 'unknown_op'


def test_set_track_rejects_an_unknown_track():
    """Una actualización de pista inexistente falla con el código compartido."""
    doc = {'version': 1, 'name': 'x', 'sample_rate': 48000, 'tracks': [], 'clips': [], 'markers': []}

    with pytest.raises(ops.OpError) as caught:
        ops.apply(doc, {'type': 'setTrack', 'id': 'missing', 'changes': {'mute': True}})

    assert caught.value.code == 'unknown_track'
