"""Reintentos de una pista que sale corta (spec 011, D-1, AC-3), con un motor falso que no carga ningún modelo."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

from content_studio.music.engines.base import MusicEngine
from content_studio.music.engines.registry import MODELS
from content_studio.music.music_main import render


def _tone(path: Path, seconds: float) -> None:
    """Un WAV de `seconds` s: lo que escribiría el motor."""
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={seconds}', path],
        check=True,
    )


class FakeEngine(MusicEngine):
    """Motor falso: cada generación escribe una pista de la duración siguiente de la lista (la última se repite)."""

    def __init__(self, lengths: list[float]) -> None:
        super().__init__(MODELS['acestep'])
        self.lengths = lengths
        self.calls = 0

    def generate(self, jobs, a) -> None:
        for _, output in jobs:
            seconds = self.lengths[min(self.calls, len(self.lengths) - 1)]
            self.calls += 1
            _tone(output, seconds)


def _result(output: Path) -> dict:
    return json.loads(output.with_suffix('.result.json').read_text(encoding='utf-8'))


def test_ac3_a_track_that_always_ends_short_is_tried_three_times_and_marked(tmp_path):
    out = tmp_path / 'acestep-lofi.wav'
    engine = FakeEngine([20])

    render(engine, [({}, out)], argparse.Namespace(duration=30))

    assert engine.calls == 3
    assert _result(out)['warning'] == 'music_short'
    assert _result(out)['duration'] == pytest.approx(20, abs=0.1)


def test_ac3_a_track_long_enough_is_generated_once_without_a_warning(tmp_path):
    out = tmp_path / 'acestep-lofi.wav'
    engine = FakeEngine([40])

    render(engine, [({}, out)], argparse.Namespace(duration=30))

    assert engine.calls == 1
    assert _result(out)['warning'] is None


def test_ac3_when_every_try_is_short_the_longest_one_is_kept(tmp_path):
    out = tmp_path / 'acestep-lofi.wav'
    engine = FakeEngine([20, 25, 15])

    render(engine, [({}, out)], argparse.Namespace(duration=30))

    assert _result(out)['duration'] == pytest.approx(25, abs=0.1)
    assert _result(out)['warning'] == 'music_short'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['acestep-lofi.result.json', 'acestep-lofi.wav']
