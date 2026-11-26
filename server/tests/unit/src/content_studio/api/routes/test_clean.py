"""Rutas del limpiador (spec 013, ciclo 6: AC-7): ver y replanificar los cortes, guardarlos y encolar el render."""

from __future__ import annotations

import json
import time

from content_studio.clean import cuts
from content_studio.db import jobs as store
from content_studio.db.connection import connect

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
PARAMS = {'input': 'entrada.wav', 'model': 'small', 'language': 'es', 'min_gap': 0.5, 'padding': 0.15, 'edges': True}


def _done_analysis(api, kind: str = 'clean.analyze') -> int:
    """Un trabajo de análisis terminado con su cuts.json y su transcripción en disco."""
    folder = api.tmp / 'job'
    transcript = folder / 'transcript.json'
    folder.mkdir(parents=True, exist_ok=True)
    transcript.write_text(json.dumps(TRANSCRIPT), encoding='utf-8')
    cuts.save(
        folder,
        {
            'params': {'min_gap': 0.5, 'padding': 0.15, 'edges': True},
            'model': 'small',
            'language': 'es',
            'duration': 3.5,
            'transcript': str(transcript),
            'cuts': [
                {'start': 0.55, 'end': 1.05, 'enabled': True},
                {'start': 2.45, 'end': 3.35, 'enabled': True},
            ],
        },
    )
    conn = connect(api.tmp / 'base.db')
    job_id = store.insert(conn, kind, 'gpu', PARAMS, group_key=None)
    conn.execute("UPDATE jobs SET status = 'done', output_dir = ? WHERE id = ?", (str(folder), job_id))
    return job_id


def test_ac7_plan_replans_without_the_gpu_in_under_200_ms(api):
    """AC-7: cambiar el hueco mínimo responde en menos de 200 ms y recalcula los cortes sin editar."""
    job_id = _done_analysis(api)
    body = {'min_gap': 0.8, 'padding': 0.15, 'edges': True}
    # La primera petición de la app paga el arranque del TestClient: el AC mide la respuesta en régimen.
    api.client.post(f'/clean/{job_id}/plan', json=body, headers=api.headers)

    started = time.monotonic()
    response = api.client.post(f'/clean/{job_id}/plan', json=body, headers=api.headers)
    elapsed = time.monotonic() - started

    assert response.status_code == 200
    assert elapsed < 0.2
    assert [(c['start'], c['end']) for c in response.json()['cuts']] == [(2.45, 3.35)]


def test_ac7_edited_cuts_survive_a_replan_after_saving(api):
    """AC-7: un corte editado a mano y guardado con PUT se conserva al replanificar."""
    job_id = _done_analysis(api)
    edited = [{'start': 0.9, 'end': 1.0, 'enabled': True, 'edited': True}]

    saved = api.client.put(f'/clean/{job_id}/cuts', json={'cuts': edited}, headers=api.headers)
    replanned = api.client.post(
        f'/clean/{job_id}/plan', json={'min_gap': 0.5, 'padding': 0.15, 'edges': True}, headers=api.headers
    )

    assert saved.status_code == 200
    assert cuts.load(api.tmp / 'job')['cuts'][0]['edited'] is True
    assert (0.9, 1.0) in [(c['start'], c['end']) for c in replanned.json()['cuts']]


def test_get_returns_the_cuts_document_of_a_finished_analysis(api):
    """El documento de cortes (parámetros, duración, cortes) se lee por el id del análisis."""
    job_id = _done_analysis(api)

    response = api.client.get(f'/clean/{job_id}', headers=api.headers)

    assert response.status_code == 200
    assert response.json()['duration'] == 3.5
    assert len(response.json()['cuts']) == 2


def test_render_enqueues_a_clean_render_job_with_the_analysis_folder(api):
    """Renderizar encola `clean.render` con el original del análisis y su carpeta de cortes."""
    job_id = _done_analysis(api)

    response = api.client.post(f'/clean/{job_id}/render', headers=api.headers)

    assert response.status_code == 201
    body = response.json()
    assert body['kind'] == 'clean.render'
    assert body['params'] == {'input': 'entrada.wav', 'analysis': str(api.tmp / 'job')}


def test_a_job_that_is_not_a_clean_analysis_is_refused(api):
    """Un trabajo de otro tipo no tiene cortes: 409 con el código `job_not_clean`."""
    job_id = _done_analysis(api, kind='narration')

    response = api.client.get(f'/clean/{job_id}', headers=api.headers)

    assert response.status_code == 409
    assert response.json()['code'] == 'job_not_clean'


def test_ac8_revision_with_speakers(api):
    """AC-8: la revisión entrega cada palabra con su hablante y el mapa de hablantes con nombres y colores."""
    job_id = _done_analysis(api)
    folder = api.tmp / 'job'
    turns = folder / 'diarization' / 'turns.json'
    turns.parent.mkdir(parents=True, exist_ok=True)
    turns.write_text(
        json.dumps(
            {
                'exclusive_diarization': [
                    {'start': 0.0, 'end': 1.5, 'speaker': 'SPEAKER_00'},
                    {'start': 1.5, 'end': 3.5, 'speaker': 'SPEAKER_01'},
                ]
            }
        ),
        encoding='utf-8',
    )
    (turns.parent / 'speakers.json').write_text(
        json.dumps(
            {
                'SPEAKER_00': {'name': 'Ana', 'color': '#2563eb'},
                'SPEAKER_01': {'name': 'Hablante 2', 'color': '#dc2626'},
            }
        ),
        encoding='utf-8',
    )
    document = json.loads((folder / 'cuts.json').read_text(encoding='utf-8'))
    document['diarization'] = str(turns)
    (folder / 'cuts.json').write_text(json.dumps(document), encoding='utf-8')

    body = api.client.get(f'/clean/{job_id}', headers=api.headers).json()

    assert [word['speaker'] for word in body['words']] == ['SPEAKER_00', 'SPEAKER_00', 'SPEAKER_01']
    assert body['speakers']['SPEAKER_00'] == {'name': 'Ana', 'color': '#2563eb'}
