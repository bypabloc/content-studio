"""Render final del limpiador (spec 013, D-4 y D-5): archivo limpio, exportaciones e informe, con ffmpeg real."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from content_studio.clean import cuts, render_main
from content_studio.common import ffmpeg as ff

# Transcripción de AC-1 (3.5 s) y cortes de AC-1: quedan tres tramos de 0.55, 1.4 y 0.15 s.
TRANSCRIPT = {
    'language': 'es',
    'language_probability': 0.99,
    'duration': 3.5,
    'segments': [
        {
            'start': 0.0,
            'end': 2.3,
            'text': 'hola mundo buenas',
            'words': [
                {'start': 0.0, 'end': 0.4, 'word': 'hola', 'probability': 0.9},
                {'start': 1.2, 'end': 1.6, 'word': 'mundo', 'probability': 0.9},
                {'start': 1.9, 'end': 2.3, 'word': 'buenas', 'probability': 0.9},
            ],
        }
    ],
}
CUTS = [
    {'start': 0.55, 'end': 1.05, 'enabled': True},
    {'start': 2.45, 'end': 3.35, 'enabled': True},
]


def _analysis(folder: Path, source_duration: float = 3.5) -> Path:
    transcript = folder / 'transcript.json'
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(json.dumps(TRANSCRIPT), encoding='utf-8')
    cuts.save(
        folder,
        {
            'params': {'min_gap': 0.5, 'padding': 0.15, 'edges': True},
            'model': 'small',
            'language': 'es',
            'duration': source_duration,
            'transcript': str(transcript),
            'cuts': CUTS,
        },
    )
    return folder


def test_ac3_and_ac5_the_audio_render_writes_the_clean_file_the_exports_and_the_report(tmp_path: Path):
    """El render de audio escribe el limpio (2.1 s menos las uniones), la transcripción, SRT, EDL, XML e informe."""
    source = tmp_path / 'entrada.wav'
    ff.ffmpeg('-y', '-f', 'lavfi', '-i', 'sine=frequency=220:duration=3.5', '-ac', '1', '-ar', '48000', str(source))
    analysis = _analysis(tmp_path / 'analysis')
    out = tmp_path / 'out'

    report = render_main.run(source, analysis, out, nvenc=False)

    for name in (
        'clean.wav',
        'transcript.txt',
        'transcript.json',
        'subtitles.srt',
        'cuts.edl',
        'cuts.xml',
        'report.json',
    ):
        assert (out / name).exists(), name
    # AC-11: el informe dice lo que suena.
    assert abs(ff.probe_duration(out / 'clean.wav') - report['duration_after']) <= 1e-3
    assert report['duration_before'] == 3.5
    assert report['duration_after'] == 2.1
    assert report['cuts'] == 2
    assert json.loads((out / 'report.json').read_text(encoding='utf-8'))['removed_seconds'] == 1.4
    assert 'hola mundo buenas' in (out / 'transcript.txt').read_text(encoding='utf-8')
    assert (out / 'cuts.edl').read_text(encoding='utf-8').count('AA/V') == 3


def test_ac4_the_video_render_keeps_the_frame_rate_and_writes_the_clean_mp4(tmp_path: Path):
    """Con video, el limpio sale en MP4 a la misma tasa de cuadros que la fuente (30 fps)."""
    source = tmp_path / 'entrada.mp4'
    ff.ffmpeg(
        '-y', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=30:duration=3.5',
        '-f', 'lavfi', '-i', 'sine=frequency=220:duration=3.5',
        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(source),
    )  # fmt: skip
    analysis = _analysis(tmp_path / 'analysis')
    out = tmp_path / 'out'

    render_main.run(source, analysis, out, nvenc=False)

    assert (out / 'clean.mp4').exists()
    assert ff.frame_rate(out / 'clean.mp4') == '30/1'
    assert (out / 'cuts.xml').read_text(encoding='utf-8').startswith('<?xml')


def _stream_seconds(path: Path, selector: str) -> float:
    """La duración de un stream (`v:0` o `a:0`) según ffprobe, no la del contenedor."""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', selector, '-show_entries', 'stream=duration', '-of', 'csv=p=0',
         str(path)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    return float(result.stdout.strip())


def test_the_video_render_audio_lasts_as_long_as_the_video_within_half_a_frame(tmp_path: Path):
    """El audio del video limpio no pierde 15 ms por corte: con un crossfade se desfasaría del video (AC-11)."""
    source = tmp_path / 'entrada.mp4'
    ff.ffmpeg(
        '-y', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=30:duration=3.5',
        '-f', 'lavfi', '-i', 'sine=frequency=220:duration=3.5',
        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(source),
    )  # fmt: skip
    analysis = _analysis(tmp_path / 'analysis')
    out = tmp_path / 'out'

    render_main.run(source, analysis, out, nvenc=False)

    video = _stream_seconds(out / 'clean.mp4', 'v:0')
    audio = _stream_seconds(out / 'clean.mp4', 'a:0')
    assert abs(audio - video) <= 0.5 / 30, (audio, video)


def test_cuts_off_the_frame_grid_keep_the_audio_as_long_as_the_video(tmp_path: Path):
    """Con cortes entre cuadros, el video corta en cuadros enteros y el audio en el instante exacto: el audio se
    ajusta a la cuadrícula para durar lo mismo (±1 cuadro, AC-11)."""
    source = tmp_path / 'entrada.mp4'
    ff.ffmpeg(
        '-y', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=25:duration=20',
        '-f', 'lavfi', '-i', 'sine=frequency=220:duration=20',
        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(source),
    )  # fmt: skip
    transcript = tmp_path / 'analysis' / 'transcript.json'
    transcript.parent.mkdir(parents=True)
    transcript.write_text(json.dumps(TRANSCRIPT), encoding='utf-8')
    off_grid = [(0.61 + 1.9 * index, 0.61 + 1.9 * index + 0.43) for index in range(10)]
    cuts.save(
        transcript.parent,
        {
            'params': {'min_gap': 0.5, 'padding': 0.15, 'edges': True},
            'model': 'small',
            'language': 'es',
            'duration': 20.0,
            'transcript': str(transcript),
            'cuts': [{'start': start, 'end': end, 'enabled': True} for start, end in off_grid],
        },
    )
    out = tmp_path / 'out'

    report = render_main.run(source, transcript.parent, out, nvenc=False)

    video = _stream_seconds(out / 'clean.mp4', 'v:0')
    audio = _stream_seconds(out / 'clean.mp4', 'a:0')
    assert abs(audio - video) <= 0.5 / 25, (audio, video)
    assert report['duration_after'] == pytest.approx(video, abs=1e-3)  # el informe dice lo que sale en el archivo


def test_the_entry_point_takes_the_job_flags_and_writes_the_outputs_into_out(tmp_path: Path):
    """`clean.render` corre `render_main` por línea de comandos: sin `main`, el trabajo salía «done» sin archivos."""
    source = tmp_path / 'entrada.wav'
    ff.ffmpeg('-y', '-f', 'lavfi', '-i', 'sine=frequency=220:duration=3.5', '-ac', '1', '-ar', '48000', str(source))
    analysis = _analysis(tmp_path / 'analysis')
    out = tmp_path / 'out'

    assert render_main.main(['--input', str(source), '--analysis', str(analysis), '--out', str(out)]) == 0

    assert (out / 'clean.wav').exists()
    assert (out / 'report.json').exists()
