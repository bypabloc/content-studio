"""Fotograma exacto de un proyecto visual (spec 018, D-5)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio import paths


def test_ac4_editor_frame_returns_a_png_for_the_requested_project(api, monkeypatch, tmp_path: Path):
    """La ruta devuelve el fotograma exacto del proyecto, no el de una fuente aislada."""
    output = tmp_path / 'out'
    monkeypatch.setattr(paths, 'outputs_dir', lambda: output)
    created = api.client.post('/editor/projects', json={'name': 'Fotograma'}, headers=api.headers)
    assert created.status_code == 201

    response = api.client.get(
        '/editor/projects/frame',
        params={'path': created.json()['path'], 't': 0},
        headers=api.headers,
    )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert response.content[:8] == b'\x89PNG\r\n\x1a\n'
    cached = list((output / 'tmp' / 'editor-frames').glob('*.png'))
    assert len(cached) == 1

    repeated = api.client.get(
        '/editor/projects/frame',
        params={'path': created.json()['path'], 't': 0},
        headers=api.headers,
    )

    assert repeated.content == response.content
    assert len(list((output / 'tmp' / 'editor-frames').glob('*.png'))) == 1


def test_editor_frame_rejects_projects_outside_the_editor_folder(api, monkeypatch, tmp_path: Path):
    """El fotograma exacto no lee proyectos ajenos a outputs/editor."""
    monkeypatch.setattr(paths, 'outputs_dir', lambda: tmp_path / 'out')
    outside = tmp_path / 'project.json'
    outside.write_text('{}', encoding='utf-8')

    response = api.client.get('/editor/projects/frame', params={'path': str(outside), 't': 0}, headers=api.headers)

    assert response.status_code == 403
    assert response.json()['code'] == 'forbidden_path'


def test_editor_frame_rejects_negative_time(api, monkeypatch, tmp_path: Path):
    """Un tiempo negativo no se convierte en un fotograma."""
    monkeypatch.setattr(paths, 'outputs_dir', lambda: tmp_path / 'out')
    created = api.client.post('/editor/projects', json={'name': 'Fotograma'}, headers=api.headers).json()

    response = api.client.get('/editor/projects/frame', params={'path': created['path'], 't': -1}, headers=api.headers)

    assert response.status_code == 422


def test_editor_frame_cache_invalidates_when_a_visual_source_changes(api, monkeypatch, tmp_path: Path):
    """Cambiar una fuente invalida el PNG aunque project.json conserve su hash."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg no está en el PATH')
    output = tmp_path / 'out'
    monkeypatch.setattr(paths, 'outputs_dir', lambda: output)
    created = api.client.post('/editor/projects', json={'name': 'Caché'}, headers=api.headers).json()
    project_file = Path(created['path'])
    folder = project_file.parent
    source = folder / 'media' / 'clip.mp4'
    source.parent.mkdir(exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=blue:s=64x64:r=10:d=1',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            str(source),
        ],
        capture_output=True,
        check=True,
    )
    doc = created['doc']
    track = doc['tracks'][0]
    track['kind'] = 'video'
    doc['clips'] = [
        {
            'id': 'video-1',
            'track': track['id'],
            'src': 'media/clip.mp4',
            'media': 'video',
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
    project_file.write_text(json.dumps(doc), encoding='utf-8')
    params = {'path': str(project_file), 't': 0.2}

    first = api.client.get('/editor/projects/frame', params=params, headers=api.headers)
    before = source.stat().st_mtime_ns
    os.utime(source, ns=(before + 1_000_000, before + 1_000_000))
    second = api.client.get('/editor/projects/frame', params=params, headers=api.headers)

    assert first.status_code == second.status_code == 200
    assert len(list((output / 'tmp' / 'editor-frames').glob('*.png'))) == 2
