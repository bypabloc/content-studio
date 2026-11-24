"""Rutas de Subtítulos (spec 014, D-1): proyectos de `subtitle_projects` y su `subtitles.json` en disco.

Un proyecto nace al terminar su trabajo `subtitles.create` (`jobs/worker.py`); aquí se parte de uno ya registrado.
"""

from __future__ import annotations

import json
from pathlib import Path

from content_studio.api.routes import subtitles as subtitles_routes
from content_studio.db import jobs as jobs_store
from content_studio.db import subtitle_projects
from content_studio.db.connection import connect
from content_studio.subtitles.document import new_document, save
from content_studio.subtitles.sources import from_cleaner

WORDS = [
    {'word': 'hola', 'start': 0.0, 'end': 0.4},
    {'word': 'mundo', 'start': 0.5, 'end': 0.9},
]


def _project(api, name: str = 'clip') -> int:
    """Un proyecto con su documento en `<tmp>/subtitles/<name>/`, como lo deja un trabajo terminado."""
    doc_path = api.tmp / 'subtitles' / name / 'subtitles.json'
    save(from_cleaner(WORDS, source_path='clean.mp4', language='es'), doc_path)
    conn = connect(api.tmp / 'base.db')
    return subtitle_projects.insert(conn, name, 'clean.mp4', str(doc_path))


def test_list_shows_the_saved_projects(api):
    """GET /subtitles lista los proyectos con su nombre y su origen."""
    _project(api)

    response = api.client.get('/subtitles', headers=api.headers)

    assert response.status_code == 200
    assert [(p['name'], p['source_path']) for p in response.json()] == [('clip', 'clean.mp4')]


def test_get_returns_the_document_of_a_project(api):
    """El documento del proyecto se lee con GET /subtitles/{id}."""
    project_id = _project(api)

    response = api.client.get(f'/subtitles/{project_id}', headers=api.headers)

    assert response.status_code == 200
    assert response.json()['source'] == {'path': 'clean.mp4', 'kind': 'cleaner'}
    assert [cue['text'] for cue in response.json()['cues']] == ['hola mundo']


def test_put_saves_the_edited_document_and_get_returns_it(api):
    """Un PUT con el documento editado lo guarda en disco; el GET siguiente lo devuelve con el cambio."""
    project_id = _project(api)
    edited = api.client.get(f'/subtitles/{project_id}', headers=api.headers).json()
    edited['cues'][0]['text'] = 'hola a todos'

    saved = api.client.put(f'/subtitles/{project_id}', json=edited, headers=api.headers)

    assert saved.status_code == 200
    assert api.client.get(f'/subtitles/{project_id}', headers=api.headers).json()['cues'][0]['text'] == 'hola a todos'


def test_export_writes_the_format_to_the_outputs_folder_and_returns_the_path(api, monkeypatch):
    """POST /subtitles/{id}/export escribe el documento en `out/subtitles/` y devuelve su ruta; un formato malo, 422."""
    project_id = _project(api)
    out = api.tmp / 'out'
    monkeypatch.setattr(subtitles_routes.paths, 'outputs_dir', lambda *args, **kwargs: out)

    response = api.client.post(f'/subtitles/{project_id}/export', json={'format': 'srt'}, headers=api.headers)

    assert response.status_code == 200
    target = Path(response.json()['path'])
    assert target == out / 'subtitles' / f'{project_id}-clean.srt'
    assert '00:00:00,000 --> ' in target.read_text(encoding='utf-8')
    unknown = api.client.post(f'/subtitles/{project_id}/export', json={'format': 'mp3'}, headers=api.headers)
    assert unknown.status_code == 422


def test_put_rejects_a_body_without_cues(api):
    """Un documento sin lista de cues no se guarda: es un error de validación."""
    project_id = _project(api)

    response = api.client.put(f'/subtitles/{project_id}', json={'version': 1}, headers=api.headers)

    assert response.status_code == 422


def test_put_writes_the_same_json_that_load_reads(api):
    """El PUT escribe el mismo JSON que lee `document.load`."""
    project_id = _project(api)
    doc = new_document(source_path='x.wav', kind='file', language='es', cues=[])

    api.client.put(f'/subtitles/{project_id}', json=doc, headers=api.headers)

    assert json.loads((api.tmp / 'subtitles' / 'clip' / 'subtitles.json').read_text(encoding='utf-8')) == doc


def test_get_of_an_unknown_project_is_not_found(api):
    """Un id que no existe da 404 con su código."""
    response = api.client.get('/subtitles/9999', headers=api.headers)

    assert response.status_code == 404
    assert response.json()['code'] == 'subtitle_project_not_found'


def test_delete_moves_the_folder_to_trash_and_removes_the_row(api):
    """DELETE borra el registro y mueve la carpeta a `.trash/`: no borra archivos (spec 014, D-1)."""
    project_id = _project(api)

    response = api.client.delete(f'/subtitles/{project_id}', headers=api.headers)

    assert response.status_code == 204
    assert not (api.tmp / 'subtitles' / 'clip').exists()
    assert (api.tmp / 'subtitles' / '.trash' / 'clip' / 'subtitles.json').exists()
    assert api.client.get(f'/subtitles/{project_id}', headers=api.headers).status_code == 404


def test_post_queues_a_subtitles_job(api):
    """POST /subtitles encola `subtitles.create`; el proyecto aparece al terminar el trabajo."""
    response = api.client.post(
        '/subtitles', json={'origin': 'cleaner', 'input': 'analisis', 'analysis': 'carpeta'}, headers=api.headers
    )

    assert response.status_code == 201
    assert response.json()['kind'] == 'subtitles.create'
    assert response.json()['status'] == 'queued'


def test_ac6_creates_an_editor_subtitle_project_from_a_done_transcription(api, monkeypatch):
    """AC-6: una transcripción terminada de la mezcla se convierte en un proyecto 014 reutilizable por el Editor."""
    queued = api.client.post(
        '/jobs',
        json={'kind': 'transcribe', 'params': {'input': 'editor-mix.wav', 'model': 'large-v3-turbo', 'language': 'es'}},
        headers=api.headers,
    )
    assert queued.status_code == 201
    job_id = queued.json()['id']
    conn = connect(api.tmp / 'base.db')
    output_dir = api.tmp / 'out' / 'transcribe-job'
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'words.json').write_text(
        json.dumps(
            {
                'language': 'es',
                'segments': [
                    {
                        'words': [
                            {'word': 'hola', 'start': 0.0, 'end': 0.4},
                            {'word': 'mundo', 'start': 0.5, 'end': 0.9},
                        ]
                    }
                ],
            }
        ),
        encoding='utf-8',
    )
    jobs_store.update(conn, job_id, status='done', output_dir=str(output_dir))
    out = api.tmp / 'out'
    monkeypatch.setattr(subtitles_routes.paths, 'outputs_dir', lambda *args, **kwargs: out)

    created = api.client.post('/subtitles/from-transcript', json={'job_id': job_id}, headers=api.headers)

    assert created.status_code == 201
    assert created.json()['source_path'] == 'editor-mix.wav'
    document = api.client.get(f'/subtitles/{created.json()["id"]}', headers=api.headers).json()
    assert [cue['text'] for cue in document['cues']] == ['hola mundo']


def test_post_with_an_unknown_origin_is_refused(api):
    """Un origen que no existe da 422 con el código del servicio."""
    response = api.client.post('/subtitles', json={'origin': 'nada'}, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'unknown_origin'


def test_fonts_lists_the_bundled_families(api):
    """AC-8: GET /subtitles/fonts devuelve las fuentes incluidas con `bundled: true`."""
    response = api.client.get('/subtitles/fonts', headers=api.headers)

    assert response.status_code == 200
    bundled = {entry['family'] for entry in response.json() if entry['bundled']}
    assert {'Montserrat', 'Inter', 'Poppins'} <= bundled
