"""Rutas del editor (spec 017, D-3): crear, abrir y guardar con `If-Match`, recientes y fuentes que faltan.

Cubre AC-2 (guardado con hash viejo) y AC-10 (fuentes que faltan al abrir).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from content_studio import paths


@pytest.fixture
def root(api, monkeypatch):
    """Los proyectos van a una carpeta temporal, no a la `outputs_dir()` real."""
    out = api.tmp / 'out'
    monkeypatch.setattr(paths, 'outputs_dir', lambda: out)
    return out


def _create(api, name: str = 'Charla') -> dict:
    response = api.client.post('/editor/projects', json={'name': name}, headers=api.headers)
    assert response.status_code == 201
    return response.json()


def _put(api, path: str, doc: dict, if_match: str):
    return api.client.put(
        '/editor/projects', params={'path': path}, json=doc, headers={**api.headers, 'If-Match': if_match}
    )


def _recording() -> bytes:
    """Un WAV PCM mono de 24 bits y 48 kHz, como el que produce el AudioWorklet."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48000)
        audio.writeframes(b'\x00\x00\x00' * 480)
    return buffer.getvalue()


def _transparent_png() -> bytes:
    """Un PNG transparente mínimo para probar la subida de títulos rasterizados."""
    import base64

    return base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
    )


def _visual_project(project_file: Path, source: str, media: str) -> None:
    """Agrega al proyecto una fuente visual v2 para probar el endpoint de medios."""
    source_file = project_file.parent / source
    source_file.parent.mkdir(exist_ok=True)
    source_file.write_bytes(b'visual source')
    doc = json.loads(project_file.read_text(encoding='utf-8'))
    track = {**doc['tracks'][0], 'kind': 'video', 'opacity': 1, 'hidden': False}
    for key in ('volume_db', 'mute', 'solo'):
        track.pop(key, None)
    doc['tracks'] = [track]
    clip = {
        'id': 'v1',
        'track': track['id'],
        'src': source,
        'media': media,
        'src_in': 0,
        'src_out': 1,
        'start': 0,
        'fade_in': 0,
        'fade_out': 0,
        'transform': {
            'x': 0,
            'y': 0,
            'scale_x': 1,
            'scale_y': 1,
            'rotation': 0,
            'opacity': 1,
            'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
            'anchor_x': 0.5,
            'anchor_y': 0.5,
        },
        'keyframes': {},
    }
    if media == 'text':
        clip['raster'] = source
    doc['clips'] = [clip]
    project_file.write_text(json.dumps(doc), encoding='utf-8')


def test_create_writes_project_json_version_3_and_its_folders(api, root):
    """Crear un proyecto escribe `project.json` versión 3 y las carpetas `media/` y `exports/`."""
    created = _create(api)

    project_file = Path(created['path'])
    assert project_file.name == 'project.json'
    assert project_file.is_relative_to(root)
    assert (project_file.parent / 'media').is_dir()
    assert (project_file.parent / 'exports').is_dir()
    assert json.loads(project_file.read_text(encoding='utf-8'))['version'] == 3


def test_a_save_with_the_current_hash_changes_the_file(api, root):
    """Con el `If-Match` del archivo actual, el guardado sale bien y el nombre queda escrito."""
    created = _create(api)

    response = _put(api, created['path'], {**created['doc'], 'name': 'Charla editada'}, created['hash'])

    assert response.status_code == 200
    assert json.loads(Path(created['path']).read_text(encoding='utf-8'))['name'] == 'Charla editada'


def test_a_save_with_a_stale_hash_is_409_and_the_file_does_not_change(api, root):
    """AC-2: con un `If-Match` que ya no es el hash del archivo, el `PUT` responde 409 y no toca el archivo."""
    created = _create(api)
    first = _put(api, created['path'], {**created['doc'], 'name': 'uno'}, created['hash'])
    assert first.status_code == 200
    before = Path(created['path']).read_bytes()

    stale = _put(api, created['path'], {**created['doc'], 'name': 'dos'}, created['hash'])

    assert stale.status_code == 409
    assert stale.json()['code'] == 'project_changed'
    assert Path(created['path']).read_bytes() == before


def test_open_returns_the_document_and_its_hash(api, root):
    """Abrir devuelve el documento y el hash que el siguiente guardado tiene que mandar en `If-Match`."""
    created = _create(api)

    opened = api.client.get('/editor/projects', params={'path': created['path']}, headers=api.headers).json()

    assert opened['doc'] == created['doc']
    assert opened['hash'] == created['hash']


def test_a_clip_whose_source_is_missing_is_reported_on_open(api, root):
    """AC-10: al abrir, los clips cuya fuente no existe salen en `missing`; el proyecto no se cambia por eso."""
    created = _create(api)
    clip = {
        'id': 'c1',
        'track': 't1',
        'src': 'media/no-existe.wav',
        'src_in': 0,
        'src_out': 2,
        'start': 0,
        'gain_db': 0,
        'fade_in': 0,
        'fade_out': 0,
    }
    saved = _put(api, created['path'], {**created['doc'], 'clips': [clip]}, created['hash'])
    assert saved.status_code == 200

    opened = api.client.get('/editor/projects', params={'path': created['path']}, headers=api.headers).json()

    assert opened['missing'] == ['media/no-existe.wav']


def test_the_recent_list_has_the_created_project(api, root):
    """Los proyectos recientes (`editor.recent` en settings) incluyen el que acabas de crear."""
    created = _create(api)

    recent = api.client.get('/editor/projects/recent', headers=api.headers).json()

    assert created['path'] in recent['paths']


def test_uploading_a_recording_saves_it_inside_the_project_media_folder(api, root):
    """D-3/D-11: la subida devuelve una fuente relativa y no toca otros archivos."""
    created = _create(api)
    recording = _recording()

    response = api.client.post(
        '/editor/projects/media',
        params={'path': created['path']},
        content=recording,
        headers={**api.headers, 'Content-Type': 'audio/wav'},
    )

    assert response.status_code == 201
    assert response.json() == {'src': 'media/rec-001.wav', 'duration': pytest.approx(0.01)}
    assert (Path(created['path']).parent / response.json()['src']).read_bytes() == recording


def test_uploading_a_text_raster_saves_it_by_clip_and_content_hash(api, root):
    """D-2: los PNG de texto quedan en media/ con el id del clip y su SHA-256."""
    created = _create(api)
    raster = _transparent_png()
    digest = hashlib.sha256(raster).hexdigest()

    response = api.client.post(
        '/editor/projects/media',
        params={'path': created['path'], 'clip_id': 'title-1', 'sha256': digest},
        content=raster,
        headers={**api.headers, 'Content-Type': 'image/png'},
    )

    expected = f'media/text-title-1-{digest}.png'
    assert response.status_code == 201
    assert response.json() == {'src': expected}
    assert (Path(created['path']).parent / expected).read_bytes() == raster


def test_uploading_a_text_raster_rejects_a_wrong_hash(api, root):
    """La ruta del PNG no puede anunciar un hash distinto a sus bytes."""
    created = _create(api)
    response = api.client.post(
        '/editor/projects/media',
        params={'path': created['path'], 'clip_id': 'title-1', 'sha256': '0' * 64},
        content=_transparent_png(),
        headers={**api.headers, 'Content-Type': 'image/png'},
    )

    assert response.status_code == 422
    assert response.json()['code'] == 'editor_text_raster_invalid'


def test_uploading_a_non_png_as_text_raster_is_rejected(api, root):
    """La subida de texto requiere PNG y no crea archivos con bytes arbitrarios."""
    created = _create(api)
    response = api.client.post(
        '/editor/projects/media',
        params={'path': created['path'], 'clip_id': 'title-1', 'sha256': hashlib.sha256(b'bad').hexdigest()},
        content=b'bad',
        headers={**api.headers, 'Content-Type': 'image/png'},
    )

    assert response.status_code == 422
    assert response.json()['code'] == 'editor_text_raster_invalid'


def test_visual_media_serves_the_requested_video_proxy_with_query_token(api, root, monkeypatch, tmp_path: Path):
    """El compositor puede cargar el proxy sin headers y solo para fuentes del proyecto."""
    from content_studio.editor import proxy

    created = _create(api)
    project_file = Path(created['path'])
    _visual_project(project_file, 'media/source.mp4', 'video')
    cached = tmp_path / 'source.mp4'
    cached.write_bytes(b'proxy')
    monkeypatch.setattr(proxy, 'create', lambda _source, _folder: cached)

    response = api.client.get(
        '/editor/projects/media',
        params={'path': str(project_file), 'source': 'media/source.mp4', 'token': api.token},
    )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'video/mp4'
    assert response.content == b'proxy'


def test_visual_media_serves_an_image_source_with_query_token(api, root):
    """Las imágenes con alfa se sirven desde el proyecto sin pasar por el proxy de video."""
    created = _create(api)
    project_file = Path(created['path'])
    _visual_project(project_file, 'media/logo.png', 'image')

    response = api.client.get(
        '/editor/projects/media',
        params={'path': str(project_file), 'source': 'media/logo.png', 'token': api.token},
    )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert response.content == b'visual source'


def test_visual_media_serves_a_text_raster_from_the_project_media_folder(api, root):
    """El título rasterizado se entrega como una fuente de imagen del proyecto."""
    created = _create(api)
    project_file = Path(created['path'])
    _visual_project(project_file, 'media/text-title-hash.png', 'text')

    response = api.client.get(
        '/editor/projects/media',
        params={'path': str(project_file), 'source': 'media/text-title-hash.png', 'token': api.token},
    )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert response.content == b'visual source'


def test_visual_media_requires_a_query_token(api, root):
    """La ruta de medios rechaza solicitudes de elementos multimedia sin token."""
    created = _create(api)

    response = api.client.get('/editor/projects/media', params={'path': created['path'], 'source': 'media/a.png'})

    assert response.status_code == 401


def test_visual_media_rejects_sources_not_referenced_by_the_project(api, root, tmp_path: Path):
    """La URL de medios del editor no habilita la lectura de rutas locales arbitrarias."""
    created = _create(api)
    source = tmp_path / 'private.png'
    source.write_bytes(b'private')

    response = api.client.get(
        '/editor/projects/media',
        params={'path': created['path'], 'source': str(source), 'token': api.token},
    )

    assert response.status_code == 404


def test_uploading_multiple_recordings_never_overwrites_an_existing_take(api, root):
    """Cada toma recibe un nombre nuevo, incluso si el primer número ya existe."""
    created = _create(api)
    first = Path(created['path']).parent / 'media' / 'rec-001.wav'
    first.write_bytes(b'toma anterior')

    response = api.client.post(
        '/editor/projects/media',
        params={'path': created['path']},
        content=_recording(),
        headers={**api.headers, 'Content-Type': 'audio/wav'},
    )

    assert response.status_code == 201
    assert response.json()['src'] == 'media/rec-002.wav'
    assert first.read_bytes() == b'toma anterior'


def test_uploading_a_non_recording_wav_is_rejected(api, root):
    """La subida rechaza WAV que no sea PCM mono de 24 bits y 48 kHz."""
    created = _create(api)
    response = api.client.post(
        '/editor/projects/media',
        params={'path': created['path']},
        content=b'not a wav',
        headers={**api.headers, 'Content-Type': 'audio/wav'},
    )

    assert response.status_code == 422
    assert response.json()['code'] == 'editor_recording_invalid'


def test_uploading_a_recording_outside_an_editor_project_is_forbidden(api, root):
    """La subida no acepta destinos fuera de outputs/editor."""
    response = api.client.post(
        '/editor/projects/media',
        params={'path': str(api.tmp / 'otro' / 'project.json')},
        content=_recording(),
        headers={**api.headers, 'Content-Type': 'audio/wav'},
    )

    assert response.status_code == 403
    assert response.json()['code'] == 'forbidden_path'


def test_an_unknown_project_is_404(api, root):
    """Un proyecto que no existe responde 404 con su código del catálogo."""
    missing = root / 'editor' / 'no-existe' / 'project.json'

    response = api.client.get('/editor/projects', params={'path': str(missing)}, headers=api.headers)

    assert response.status_code == 404
    assert response.json()['code'] == 'editor_project_not_found'


def test_a_path_outside_the_editor_folder_is_403(api, root):
    """Un proyecto fuera de la carpeta del editor no se abre: 403 `forbidden_path`."""
    outside = api.tmp / 'otro' / 'project.json'

    response = api.client.get('/editor/projects', params={'path': str(outside)}, headers=api.headers)

    assert response.status_code == 403
    assert response.json()['code'] == 'forbidden_path'


def test_editor_frame_returns_a_png_for_the_requested_project(api, root, monkeypatch):
    """La ruta devuelve el fotograma exacto del proyecto y reutiliza su caché."""
    from content_studio.editor import render_video

    def write_png(_doc, _folder, _time, output):
        output.write_bytes(b'\x89PNG\r\n\x1a\nmock-frame')

    monkeypatch.setattr(render_video, 'render_frame', write_png)
    created = _create(api, 'Fotograma')
    params = {'path': created['path'], 't': 0}

    response = api.client.get('/editor/projects/frame', params=params, headers=api.headers)

    assert response.status_code == 200, response.text
    assert response.headers['content-type'] == 'image/png'
    assert response.content[:8] == b'\x89PNG\r\n\x1a\n'
    cached = list((root / 'tmp' / 'editor-frames').glob('*.png'))
    assert len(cached) == 1
    repeated = api.client.get('/editor/projects/frame', params=params, headers=api.headers)
    assert repeated.content == response.content
    assert len(list((root / 'tmp' / 'editor-frames').glob('*.png'))) == 1


def test_editor_frame_rejects_projects_outside_the_editor_folder(api):
    """El fotograma exacto no lee proyectos ajenos a outputs/editor."""
    outside = api.tmp / 'project.json'
    outside.write_text('{}', encoding='utf-8')

    response = api.client.get('/editor/projects/frame', params={'path': str(outside), 't': 0}, headers=api.headers)

    assert response.status_code == 403
    assert response.json()['code'] == 'forbidden_path'


def test_editor_frame_rejects_negative_time(api, root):
    """Un tiempo negativo no se convierte en un fotograma."""
    created = _create(api, 'Fotograma')

    response = api.client.get('/editor/projects/frame', params={'path': created['path'], 't': -1}, headers=api.headers)

    assert response.status_code == 422


def test_editor_frame_cache_invalidates_when_a_visual_source_changes(api, root):
    """Cambiar una fuente invalida el PNG aunque project.json conserve su hash."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg no está en el PATH')
    created = _create(api, 'Caché')
    project_file = Path(created['path'])
    source = project_file.parent / 'media' / 'clip.mp4'
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
    assert len(list((root / 'tmp' / 'editor-frames').glob('*.png'))) == 2
