"""Trabajo `editor.render` (spec 017, D-4): `render_main` renderiza a `exports/` y deja `result.json`."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from content_studio.editor import project, render_main, store

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


@needs_ffmpeg
def test_the_job_renders_into_the_project_exports_and_leaves_its_result(tmp_path: Path):
    """Un proyecto con un clip de 2 s renderiza `exports/<carpeta del trabajo>.wav` de 2 s y deja `result.json`."""
    project_file = store.create(tmp_path / 'editor', 'Charla', date(2026, 11, 22))
    media = project_file.parent / 'media'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=3:sample_rate=48000',
            str(media / 'tono.wav'),
        ],
        check=True,
    )
    doc, _ = store.read(project_file)
    doc['clips'] = [
        {
            'id': 'c1',
            'track': 't1',
            'src': 'media/tono.wav',
            'src_in': 0,
            'src_out': 2,
            'start': 0,
            'gain_db': 0,
            'fade_in': 0,
            'fade_out': 0,
        }
    ]
    store.write(project_file, doc, store.read(project_file)[1])
    job = tmp_path / 'jobs' / '2026-11-22-7-editor-render'
    job.mkdir(parents=True)

    code = render_main.main(['--project', str(project_file), '--format', 'wav', '--out-dir', str(job)])

    assert code == 0
    result = json.loads((job / 'result.json').read_text(encoding='utf-8'))
    assert result['status'] == 'done'
    assert Path(result['output']) == project_file.parent / 'exports' / '2026-11-22-7-editor-render.wav'
    assert result['duration'] == pytest.approx(2, abs=0.01)


def test_an_invalid_project_exits_with_2_and_renders_nothing(tmp_path: Path, capsys):
    """Un documento que no vale (un clip sin pista) no renderiza: sale con 2 y lo dice en la salida."""
    project_file = store.create(tmp_path / 'editor', 'Charla', date(2026, 11, 22))
    doc, digest = store.read(project_file)
    doc['clips'] = [
        {
            'id': 'c1',
            'track': 'no-existe',
            'src': 'media/x.wav',
            'src_in': 0,
            'src_out': 2,
            'start': 0,
            'gain_db': 0,
            'fade_in': 0,
            'fade_out': 0,
        }
    ]
    store.write(project_file, doc, digest)
    job = tmp_path / 'jobs' / 'j'
    job.mkdir(parents=True)

    code = render_main.main(['--project', str(project_file), '--out-dir', str(job)])

    assert code == 2
    assert json.loads(capsys.readouterr().out)['errors'] == [{'code': 'unknown_track', 'id': 'c1'}]
    assert not (job / 'result.json').exists()


def test_missing_sources_are_preserved_in_the_job_result(tmp_path: Path, capsys):
    """Una fuente ausente deja su ruta en result.json para que la UI permita encontrarla."""
    project_file = store.create(tmp_path / 'editor', 'Charla', date(2026, 11, 22))
    doc, digest = store.read(project_file)
    doc['clips'] = [
        {
            'id': 'c1',
            'track': 't1',
            'src': 'media/tono-ausente.wav',
            'src_in': 0,
            'src_out': 2,
            'start': 0,
            'gain_db': 0,
            'fade_in': 0,
            'fade_out': 0,
        }
    ]
    store.write(project_file, doc, digest)
    job = tmp_path / 'jobs' / 'missing-source'
    job.mkdir(parents=True)

    code = render_main.main(['--project', str(project_file), '--out-dir', str(job)])

    assert code == 3
    assert json.loads((job / 'result.json').read_text(encoding='utf-8')) == {
        'status': 'failed',
        'error': 'missing_source',
        'params': {'paths': ['media/tono-ausente.wav']},
    }
    assert json.loads(capsys.readouterr().out) == {
        'status': 'failed',
        'error': 'missing_source',
        'params': {'paths': ['media/tono-ausente.wav']},
    }


@needs_ffmpeg
def test_video_format_renders_visual_and_audio_to_its_exports_folder(tmp_path: Path, capsys):
    """El MP4 mezcla la composición visual y el grafo de audio y registra la duración y la ruta."""
    project_file = store.create(tmp_path / 'editor', 'Logo', date(2026, 11, 22))
    media = project_file.parent / 'media'
    subprocess.run(
        [
            'ffmpeg',
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=red:s=16x16:d=1',
            '-frames:v',
            '1',
            '-c:v',
            'png',
            str(media / 'logo.png'),
        ],
        check=True,
    )
    subprocess.run(
        [
            'ffmpeg',
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=1:sample_rate=48000',
            str(media / 'tone.wav'),
        ],
        check=True,
    )
    doc, digest = store.read(project_file)
    doc['canvas'] = {**project.DEFAULT_CANVAS, 'width': 320, 'height': 240, 'fps': 10}
    doc['tracks'] = [
        {'id': 'v1', 'kind': 'video', 'name': 'Video', 'opacity': 1, 'hidden': False, 'locked': False},
        {'id': 'a1', 'kind': 'audio', 'name': 'Audio', 'volume_db': 0, 'mute': False, 'solo': False, 'locked': False},
    ]
    doc['clips'] = [
        {
            'id': 'logo',
            'track': 'v1',
            'src': 'media/logo.png',
            'media': 'image',
            'src_in': 0,
            'src_out': 0.5,
            'start': 0,
            'gain_db': 0,
            'fade_in': 0,
            'fade_out': 0,
            'transform': {
                'x': 0,
                'y': 0,
                'scale_x': 1,
                'scale_y': 1,
                'rotation': 0,
                'opacity': 1,
                'anchor_x': 0.5,
                'anchor_y': 0.5,
                'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
            },
            'keyframes': {},
        },
        {
            'id': 'tone',
            'track': 'a1',
            'src': 'media/tone.wav',
            'src_in': 0,
            'src_out': 0.5,
            'start': 0,
            'gain_db': 0,
            'fade_in': 0,
            'fade_out': 0,
        },
    ]
    store.write(project_file, doc, digest)
    job = tmp_path / 'jobs' / '2026-11-22-8-editor-video'
    job.mkdir(parents=True)

    code = render_main.main(['--project', str(project_file), '--format', 'mp4-h264', '--out-dir', str(job)])

    assert code == 0
    result = json.loads((job / 'result.json').read_text(encoding='utf-8'))
    assert result['status'] == 'done'
    assert Path(result['output']) == project_file.parent / 'exports' / '2026-11-22-8-editor-video.mp4'
    assert result['duration'] == pytest.approx(0.5, abs=0.11)
    graph = Path(result['output']).with_suffix('.filter')
    assert graph.is_file() and 'overlay=' in graph.read_text(encoding='utf-8')
    streams = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', result['output']],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert streams == ['video', 'audio']
    assert json.loads(capsys.readouterr().out) == result

    audio_job = tmp_path / 'jobs' / 'audio-only'
    audio_job.mkdir(parents=True)
    audio_code = render_main.main(
        ['--project', str(project_file), '--format', 'wav', '--name', 'audio-only', '--out-dir', str(audio_job)]
    )
    audio_result = json.loads((audio_job / 'result.json').read_text(encoding='utf-8'))
    assert audio_code == 0
    assert audio_result['status'] == 'done'
    assert Path(audio_result['output']).name == 'audio-only.wav'
    assert audio_result['duration'] == pytest.approx(0.5, abs=0.01)
    assert json.loads(capsys.readouterr().out) == audio_result


def test_missing_visual_source_is_preserved_in_the_job_result(tmp_path: Path, capsys):
    """Una imagen ausente deja su ruta relativa para que el editor permita encontrarla."""
    project_file = store.create(tmp_path / 'editor', 'Logo', date(2026, 11, 22))
    doc, digest = store.read(project_file)
    doc['tracks'] = [{'id': 'v1', 'kind': 'video', 'name': 'Video', 'opacity': 1, 'hidden': False, 'locked': False}]
    doc['clips'] = [
        {
            'id': 'logo',
            'track': 'v1',
            'src': 'media/missing.png',
            'media': 'image',
            'src_in': 0,
            'src_out': 1,
            'start': 0,
            'gain_db': 0,
            'fade_in': 0,
            'fade_out': 0,
            'transform': {
                'x': 0,
                'y': 0,
                'scale_x': 1,
                'scale_y': 1,
                'rotation': 0,
                'opacity': 1,
                'anchor_x': 0.5,
                'anchor_y': 0.5,
                'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
            },
            'keyframes': {},
        }
    ]
    store.write(project_file, doc, digest)
    job = tmp_path / 'jobs' / 'missing-visual'
    job.mkdir(parents=True)

    code = render_main.main(['--project', str(project_file), '--format', 'mp4-h264', '--out-dir', str(job)])

    result = {'status': 'failed', 'error': 'missing_source', 'params': {'paths': ['media/missing.png']}}
    assert code == 3
    assert json.loads((job / 'result.json').read_text(encoding='utf-8')) == result
    assert json.loads(capsys.readouterr().out) == result
