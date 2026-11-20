"""Muestras de 10 s por estilo (spec 011, D-3, AC-5): solo se generan las que faltan, salvo con `force`."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from content_studio.music import samples_main
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


def test_ac5_all_samples_present_generates_nothing(tmp_path):
    for key in FIVE:
        _tone(tmp_path / f'{key}.wav', 10)
    engine = FakeEngine()

    assert render_samples(engine, FIVE, tmp_path, force=False) == []
    assert engine.generated == []


def test_main_runs_inside_the_acestep_venv_and_generates_the_missing_samples(tmp_path, monkeypatch, capsys):
    """Entrada de `python -m content_studio.music.samples_main`: corre dentro del venv de ACE-Step."""
    engine = FakeEngine()
    venvs = []

    class Spec:
        def path_venv(self):
            return tmp_path / 'venv'

        def create(self):
            return engine

    monkeypatch.setitem(samples_main.MODELS, 'acestep', Spec())
    monkeypatch.setattr(samples_main, 'SAMPLES', tmp_path / 'samples')
    monkeypatch.setattr(samples_main.process, 'console_utf8', lambda: None)
    monkeypatch.setattr(samples_main.process, 'use_venv', lambda venv, readme, module: venvs.append((venv, module)))
    monkeypatch.setattr(sys, 'argv', ['samples_main', '--styles', 'lofi-chill', 'corporate'])

    samples_main.main()

    assert venvs == [(tmp_path / 'venv', 'content_studio.music.samples_main')]
    assert engine.generated == ['lofi-chill', 'corporate']
    assert '2 sample(s) generated' in capsys.readouterr().out
