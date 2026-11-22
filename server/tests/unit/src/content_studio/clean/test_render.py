"""Render del limpiador (spec 013, ciclos 3 y 4: AC-3 y AC-4). Usa ffmpeg real con medios generados en la prueba."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from content_studio.clean import render
from content_studio.common import ffmpeg as ff

# cspell:ignore crossfades geq lavfi yuv nvenc: nombres de pruebas, filtros de ffmpeg y formato de píxel.

# --- Audio (AC-3) -----------------------------------------------------------------------------------------------------
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


# --- Video (AC-4) -----------------------------------------------------------------------------------------------------
FPS = 30
# Fixture de 10 s a 30 fps. En el bloque de 16×16 de la esquina, R = 2·(N mod 128) y G = 60·floor(N/128), con N el
# número de cuadro. Así se lee el cuadro del píxel (0, 0) sin OCR, con tolerancia de ±1 cuadro.
VIDEO_GEQ = (
    'color=c=black:s=320x240:r=30:d=10,format=rgb24,'
    "geq=r='if(lt(X\\,16)*lt(Y\\,16)\\,2*mod(N\\,128)\\,0)':"
    "g='if(lt(X\\,16)*lt(Y\\,16)\\,60*floor(N/128)\\,0)':b=0"
)
# Voz sintética de 10 s: 0–2 s, 3–4 s y 6–8 s. Cortes con min_gap 0.5 y padding 0.15: [2.15–2.85], [4.15–5.85],
# [8.15–9.85]. Tramos a conservar: 2.15 + 1.30 + 2.30 = 5.75 s, que son 173 cuadros.
VIDEO_SPEECH = '0.5*sin(2*PI*220*t)*(between(t\\,0\\,2)+between(t\\,3\\,4)+between(t\\,6\\,8))'
VIDEO_KEEP = [(0.0, 2.15), (2.85, 4.15), (5.85, 8.15)]


def _make_video_source(path: Path) -> None:
    ff.ffmpeg(
        '-y',
        '-f', 'lavfi', '-i', VIDEO_GEQ,
        '-f', 'lavfi', '-i', f'aevalsrc={VIDEO_SPEECH}:s=48000:d=10',
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-qp', '0', '-pix_fmt', 'yuv444p',
        '-c:a', 'aac', '-b:a', '192k',
        str(path),
    )  # fmt: skip


def _frame_numbers(path: Path) -> list[int]:
    """Número de cuadro de origen de cada cuadro del archivo, leído del píxel (0, 0)."""
    raw = subprocess.run(
        [
            'ffmpeg', '-v', 'error', '-i', str(path),
            # format=rgb24 antes del recorte: en yuv420p un recorte de 1×1 deja el croma con ancho 0.
            '-vf', 'format=rgb24,crop=1:1:0:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-',
        ],
        capture_output=True,
        check=True,
    ).stdout  # fmt: skip
    return [round(raw[i + 1] / 60) * 128 + round(raw[i] / 2) for i in range(0, len(raw), 3)]


def test_ac4_first_frame_of_each_kept_segment_is_within_one_frame(tmp_path: Path):
    """AC-4: el primer cuadro de cada tramo conservado es el esperado ±1 cuadro."""
    source = tmp_path / 'entrada.mp4'
    out = tmp_path / 'limpio.mp4'
    _make_video_source(source)

    render.render_video(source, VIDEO_KEEP, out, nvenc=False)

    frames = _frame_numbers(out)
    # Tramo 1 empieza en el cuadro 0; tramo 2 en el 86 (2.85 s); tramo 3 en el 176 (5.85 s).
    assert abs(frames[0] - 0) <= 1
    assert abs(frames[65] - 86) <= 1
    assert abs(frames[65 + 39] - 176) <= 1


def test_ac4_audio_and_video_last_the_same_within_one_frame_and_the_expected_frame_count(tmp_path: Path):
    """AC-4: el audio y el video duran lo mismo ±1 cuadro, y hay unos 173 cuadros (5.75 s a 30 fps)."""
    source = tmp_path / 'entrada.mp4'
    out = tmp_path / 'limpio.mp4'
    _make_video_source(source)

    render.render_video(source, VIDEO_KEEP, out, nvenc=False)

    video_frames = len(_frame_numbers(out))
    assert abs(video_frames - 173) <= 1
    assert abs(ff.probe_duration(out) - video_frames / FPS) <= 1 / FPS


@pytest.mark.local
def test_ac4_nvenc_render_keeps_the_same_frames(tmp_path: Path):
    """AC-4 con NVENC (solo en este equipo): mismos 173 cuadros y el mismo inicio de tramos que con libx264."""
    source = tmp_path / 'entrada.mp4'
    out = tmp_path / 'limpio.mp4'
    _make_video_source(source)

    render.render_video(source, VIDEO_KEEP, out, nvenc=True)

    frames = _frame_numbers(out)
    assert abs(len(frames) - 173) <= 1
    assert abs(frames[65] - 86) <= 1
    assert abs(frames[65 + 39] - 176) <= 1


def test_video_codec_uses_nvenc_when_available_and_x264_otherwise():
    """El codificador sale del equipo: NVENC si hay NVIDIA; si no, libx264 con CRF 18."""
    assert render.video_codec(nvenc=True) == ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '19']
    assert render.video_codec(nvenc=False) == ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']


def test_video_graph_trims_each_segment_and_concatenates_them():
    """El grafo de video tiene un trim por tramo y un concat con todos ellos."""
    graph = render.video_graph(VIDEO_KEEP)

    assert graph.count('trim=') == 3
    assert 'concat=n=3:v=1:a=0[vout]' in graph
