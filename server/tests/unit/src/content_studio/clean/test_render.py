"""Render de audio del limpiador (spec 013, ciclo 3: AC-3). Usa ffmpeg real con un WAV generado en la prueba."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_studio.clean import render
from content_studio.common import ffmpeg as ff

# cspell:ignore crossfades: nombre de la prueba del grafo de audio.

# Voz sintética: tonos en 0–1 s, 2.5–3.5 s y 5–6 s; silencio en medio. Los cortes salen de plan() con
# min_gap 0.5 y padding 0.15: [1.15–2.35] y [3.65–4.85]. Tramos a conservar: 1.15 + 1.30 + 1.15 = 3.6 s.
SPEECH = '0.5*sin(2*PI*220*t)*(between(t\\,0\\,1)+between(t\\,2.5\\,3.5)+between(t\\,5\\,6))'
KEEP = [(0.0, 1.15), (2.35, 3.65), (4.85, 6.0)]


def _make_source(path: Path) -> None:
    ff.ffmpeg('-y', '-f', 'lavfi', '-i', f'aevalsrc={SPEECH}:s=48000:d=6', '-c:a', 'pcm_s16le', str(path))


def test_ac3_audio_clean_lasts_the_expected_duration_and_has_no_long_silence(tmp_path: Path):
    """AC-3: la salida dura 3.6 s menos 15 ms por cada unión (±20 ms) y ningún silencio pasa de 0.5 + 2×0.15 s."""
    source = tmp_path / 'entrada.wav'
    out = tmp_path / 'limpio.wav'
    _make_source(source)

    render.render_audio(source, KEEP, out)

    expected = sum(e - s for s, e in KEEP) - render.FADE_SECONDS * (len(KEEP) - 1)
    assert ff.probe_duration(out) == pytest.approx(expected, abs=0.02)
    longest = max((end - start for start, end in ff.silences(out, noise_db=-50.0, minimum=0.1) if end), default=0.0)
    assert longest <= 0.5 + 2 * 0.15


def test_audio_graph_trims_each_segment_and_crossfades_between_them():
    """El filter_complex tiene un trim por tramo y un acrossfade entre cada par de tramos consecutivos."""
    graph = render.audio_graph(KEEP)

    assert graph.count('atrim=') == 3
    assert graph.count('acrossfade=d=0.015') == 2
    assert graph.rstrip().endswith('[aout]')


def test_audio_graph_fades_a_segment_shorter_than_30_ms_at_its_edges():
    """Un tramo de menos de 30 ms recibe afade de entrada y salida de 15 ms, como pide D-4."""
    graph = render.audio_graph([(0.0, 1.0), (2.0, 2.02)])

    assert 'afade=t=in:d=0.015' in graph
    assert 'afade=t=out:st=0.005:d=0.015' in graph
