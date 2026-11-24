"""Rutas de la biblioteca (spec 020): carpetas vigiladas, escaneo por la cola y miniaturas."""

from __future__ import annotations

import shutil
import subprocess
from contextlib import closing

import pytest

from content_studio.db import connection, jobs
from content_studio.library import index

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def test_folders_can_be_added_listed_and_removed(api):
    """POST, GET y DELETE de /library/folders; una ruta que no es carpeta da 422 `invalid_folder`."""
    folder = api.tmp / 'videos'
    folder.mkdir()

    created = api.client.post('/library/folders', json={'path': str(folder)}, headers=api.headers)
    listed = api.client.get('/library/folders', headers=api.headers)
    bad = api.client.post('/library/folders', json={'path': str(api.tmp / 'nada')}, headers=api.headers)
    removed = api.client.delete(f'/library/folders/{created.json()["id"]}', headers=api.headers)
    again = api.client.delete(f'/library/folders/{created.json()["id"]}', headers=api.headers)

    assert created.status_code == 201
    assert [f['name'] for f in listed.json()] == ['videos']
    assert (bad.status_code, bad.json()['code']) == (422, 'invalid_folder')
    assert removed.status_code == 204
    assert (again.status_code, again.json()['code']) == (404, 'folder_not_found')


def test_scan_enqueues_a_cpu_job_for_one_folder_or_all(api):
    """POST /library/scan encola `library.scan` (CPU) con la carpeta pedida o sin ella."""
    response = api.client.post('/library/scan', json={'folder_id': 4}, headers=api.headers)

    assert response.status_code == 201
    assert (response.json()['kind'], response.json()['params']) == ('library.scan', {'folder_id': 4})


@needs_ffmpeg
def test_thumb_of_a_video_is_a_jpeg_and_accepts_the_query_token(api, monkeypatch):
    """GET /library/thumb/{id} entrega el JPEG con `?token=` (lo pide un <img>); audio da 422 y un id ajeno, 404."""
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(api.tmp / 'home'))
    video = api.tmp / 'out' / 'clip.mp4'
    video.parent.mkdir(parents=True)
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc=size=160x120:rate=10:duration=1',
         str(video)],
        check=True,
    )  # fmt: skip
    (api.tmp / 'out' / 'a.srt').write_text('', encoding='utf-8')
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        job_id = jobs.insert(conn, 'media.convert', 'cpu', {})
        jobs.update(conn, job_id, status='done', output_dir=str(video.parent))
        video_id, subtitle_id = index.register_job(conn, jobs.get(conn, job_id))[::-1]

    thumb = api.client.get(f'/library/thumb/{video_id}?token={api.token}')
    other = api.client.get(f'/library/thumb/{subtitle_id}?token={api.token}')
    missing = api.client.get(f'/library/thumb/999?token={api.token}')

    assert (thumb.status_code, thumb.headers['content-type']) == (200, 'image/jpeg')
    assert (other.status_code, other.json()['code']) == (422, 'no_thumbnail')
    assert (missing.status_code, missing.json()['code']) == (404, 'item_not_found')
