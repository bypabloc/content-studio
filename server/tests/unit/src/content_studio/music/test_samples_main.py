"""Muestras de 10 s por estilo (spec 011, D-3, AC-5): solo se generan las que faltan, salvo con `force`."""

from __future__ import annotations

import subprocess
from pathlib import Path

from content_studio.music.engines.base import MusicEngine
from content_studio.music.engines.registry import MODELS
from content_studio.music.samples_main import render_samples


def _tone(path: Path, seconds: float) -> None:
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={seconds}', path],
        check=True,
    )


class FakeEngine(MusicEngine):
    """Motor falso: cada muestra es un tono de 10 s, y anota qué estilos generó."""

    def __init__(self) -> None:
        super().__init__(MODELS['acestep'])
        self.generated: list[str] = []

    def generate(self, jobs, a) -> None:
        for _style, output in jobs:
            self.generated.append(output.stem)
            _tone(output, 10)


FIVE = ['lofi-chill', 'lofi-jazz', 'lofi-rain', 'corporate', 'ambient']


def test_ac5_only_the_missing_samples_are_generated(tmp_path):
    for key in ['lofi-chill', 'lofi-jazz', 'lofi-rain']:
        _tone(tmp_path / f'{key}.wav', 10)
    engine = FakeEngine()

    done = render_samples(engine, FIVE, tmp_path, force=False)

    assert done == ['corporate', 'ambient']
    assert engine.generated == ['corporate', 'ambient']


def test_ac5_force_generates_all_five_again(tmp_path):
    for key in ['lofi-chill', 'lofi-jazz', 'lofi-rain']:
        _tone(tmp_path / f'{key}.wav', 10)
    engine = FakeEngine()

    done = render_samples(engine, FIVE, tmp_path, force=True)

    assert done == FIVE
    assert len(list(tmp_path.glob('*.wav'))) == 5
