"""Trabajo `editor.render` (spec 017, D-4): `render_main` renderiza a `exports/` y deja `result.json`."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from content_studio.editor import render_main, store

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
