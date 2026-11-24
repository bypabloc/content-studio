"""Rutas del asistente, spec 021 D-5: estado, idiomas, resultado y aplicar en subtítulos."""

from __future__ import annotations

import json
from contextlib import closing
from types import SimpleNamespace

from content_studio.db import connection, jobs, settings, subtitle_projects
from content_studio.llm import models
from content_studio.subtitles.document import load, new_document, save


def _done_job(api, kind, result):
    out = api.tmp / 'out' / 'llm' / kind
    out.mkdir(parents=True)
    (out / 'result.json').write_text(json.dumps(result), encoding='utf-8')
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        job_id = jobs.insert(conn, kind, 'gpu', {})
        jobs.update(conn, job_id, status='done', output_dir=str(out))
    return job_id


def _project(api):
    cue = {'id': 1, 'start': 0.0, 'end': 1.0, 'text': 'Hola Clinicae', 'words': []}
    doc = api.tmp / 'subtitles.json'
    save(new_document(source_path='demo.mp4', kind='import', language='es', cues=[cue]), doc)
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        return subtitle_projects.insert(conn, 'demo', 'demo.mp4', str(doc)), doc


def test_status_reports_the_choice_and_nothing_loaded(api, monkeypatch):
    """Sin motores, nada instalado; el elegido es el ★ y, sin worker, no hay modelo cargado."""
    monkeypatch.setattr('content_studio.api.routes.llm.paths.engines_dir', lambda db=None: api.tmp / 'engines')
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        settings.set_value(conn, 'llm.enabled', False)

    body = api.client.get('/llm/status', headers=api.headers).json()

    assert body['enabled'] is False
    assert body['runtime_installed'] is False
    assert body['selected'] == models.RECOMMENDED
    assert {model['model'] for model in body['models']} == {'gemma-4-e4b', 'qwen3.5-9b'}
    assert (body['loaded'], body['release_in']) == (None, None)


def test_status_shows_the_warm_model_and_when_it_is_released(api, monkeypatch):
    """Con el asistente caliente, el estado dice qué modelo está cargado y en cuántos segundos se libera."""
    warm = SimpleNamespace(running=True, runtime=SimpleNamespace(model='qwen3.5-9b'), release_in=lambda: 105.0)
    api.app.state.worker = SimpleNamespace(llm=warm)

    body = api.client.get('/llm/status', headers=api.headers).json()

    assert (body['loaded'], body['release_in']) == ('qwen3.5-9b', 105.0)


def test_languages_have_the_star_on_english(api):
    """GET /llm/languages trae los idiomas con su nombre propio y ★ en el inglés."""
    body = api.client.get('/llm/languages', headers=api.headers).json()
    assert {'code': 'en', 'name': 'English', 'recommended': True} in body


def test_result_returns_the_proposal_or_404(api):
    """El resultado de un llm.* terminado; otro trabajo o uno sin result.json dan 404."""
    job_id = _done_job(api, 'llm.music_caption', {'caption': 'piano, no vocals'})
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        other = jobs.insert(conn, 'narration', 'gpu', {})
        pending = jobs.insert(conn, 'llm.publish', 'gpu', {})

    assert api.client.get(f'/llm/jobs/{job_id}/result', headers=api.headers).json()['caption'] == 'piano, no vocals'
    assert api.client.get(f'/llm/jobs/{other}/result', headers=api.headers).json()['code'] == 'job_not_found'
    assert api.client.get(f'/llm/jobs/{pending}/result', headers=api.headers).json()['code'] == 'llm_result_not_found'


def test_apply_saves_only_the_accepted_correction(api):
    """Aplicar una corrección aceptada cambia el documento del proyecto y lo devuelve."""
    project_id, doc = _project(api)
    proposal = {
        'cues': [{'id': 1, 'original': 'Hola Clinicae', 'text': 'Hola Klinikae', 'words': None, 'review': False}]
    }
    job_id = _done_job(api, 'llm.subtitles_correct', proposal)

    response = api.client.post(
        f'/llm/subtitles/{project_id}/apply', json={'job_id': job_id, 'accepted': [1]}, headers=api.headers
    )

    assert response.status_code == 200
    assert load(doc)['cues'][0]['text'] == 'Hola Klinikae'


def test_apply_a_translation_adds_its_track(api):
    """Aceptar una traducción guarda la pista en tracks[<idioma>]."""
    project_id, doc = _project(api)
    proposal = {
        'language': 'pt',
        'cues': [{'id': 1, 'start': 0.0, 'end': 1.0, 'text': 'Olá', 'original': 'Hola', 'flag': None}],
    }
    job_id = _done_job(api, 'llm.subtitles_translate', proposal)

    api.client.post(f'/llm/subtitles/{project_id}/apply', json={'job_id': job_id}, headers=api.headers)

    assert load(doc)['tracks']['pt'][0]['text'] == 'Olá'


def test_apply_rejects_a_task_that_is_not_for_subtitles_and_a_missing_project(api):
    """Una propuesta de música no se aplica a subtítulos (422); un proyecto que no existe da 404."""
    project_id, _ = _project(api)
    job_id = _done_job(api, 'llm.music_caption', {'caption': 'x'})

    wrong = api.client.post(f'/llm/subtitles/{project_id}/apply', json={'job_id': job_id}, headers=api.headers)
    missing = api.client.post('/llm/subtitles/999/apply', json={'job_id': job_id}, headers=api.headers)

    assert (wrong.status_code, wrong.json()['code']) == (422, 'llm_not_applicable')
    assert (missing.status_code, missing.json()['code']) == (404, 'subtitle_project_not_found')
