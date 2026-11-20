"""Duración exacta de la música (spec 011, D-1): lo que se pide al motor y el corte a lo pedido (AC-1, AC-2)."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import pytest
import soundfile as sf

from content_studio.music.duration import finish, fit, plan_duration


def _tone(path: Path, seconds: int) -> None:
    """Un tono de `seconds` s en mono: el material sintético del corte."""
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=440:duration={seconds}',
            '-ac',
            '1',
            path,
        ],
        check=True,
    )


def _rms(data, rate: int, start: float, end: float) -> float:
    """RMS del tramo [start, end) en segundos."""
    segment = data[int(start * rate) : int(end * rate)]
    return float((segment**2).mean() ** 0.5)


def test_ac1_plan_asks_for_the_target_plus_a_margin_capped_at_the_engine_max():
    assert [plan_duration(30, 600), plan_duration(60, 600), plan_duration(590, 600), plan_duration(700, 600)] == [
        40,
        75,
        600,
        600,
    ]


def test_ac2_fit_cuts_to_the_target_with_a_two_second_fade(tmp_path):
    track = tmp_path / 'track.wav'
    _tone(track, 34)

    fit(track, 30)

    data, rate = sf.read(track)
    assert len(data) / rate == pytest.approx(30, abs=0.01)
    loud = _rms(data, rate, 25, 25.5)
    last_half_second = _rms(data, rate, 29.5, 30)
    assert 20 * math.log10(last_half_second / loud) <= -20


def test_a_short_target_fades_over_a_third_of_it(tmp_path):
    track = tmp_path / 'short.wav'
    _tone(track, 10)

    fit(track, 4)

    data, rate = sf.read(track)
    assert len(data) / rate == pytest.approx(4, abs=0.01)
    # El fade ocupa un tercio de 4 s: desde el segundo 2,67 hasta el 4. El último 0,2 s ya está casi en silencio.
    assert _rms(data, rate, 3.8, 4) < _rms(data, rate, 0.5, 0.7) / 10


def test_finish_fits_a_track_that_reaches_the_target_and_leaves_a_short_one_alone(tmp_path):
    long_track, short_track = tmp_path / 'long.wav', tmp_path / 'short.wav'
    _tone(long_track, 40)
    _tone(short_track, 20)

    assert finish(long_track, 30) == 30
    assert finish(short_track, 30) == pytest.approx(20, abs=0.1)

    assert sf.info(long_track).duration == pytest.approx(30, abs=0.01)
    assert sf.info(short_track).duration == pytest.approx(20, abs=0.1)
