"""Rutas del editor (spec 017, D-3): crear, abrir y guardar con `If-Match`, recientes y fuentes que faltan.

Cubre AC-2 (guardado con hash viejo) y AC-10 (fuentes que faltan al abrir).
"""

from __future__ import annotations

import io
import json
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


def test_create_writes_project_json_version_1_and_its_folders(api, root):
    """Crear un proyecto escribe `project.json` (versión 1) y las carpetas `media/` y `exports/`."""
    created = _create(api)

    project_file = Path(created['path'])
    assert project_file.name == 'project.json'
    assert project_file.is_relative_to(root)
    assert (project_file.parent / 'media').is_dir()
    assert (project_file.parent / 'exports').is_dir()
    assert json.loads(project_file.read_text(encoding='utf-8'))['version'] == 1


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
