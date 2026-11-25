"""Resultado de una diarización por la API (spec 037, AC-4): turnos, hablantes, archivos y WAV por hablante."""

from __future__ import annotations

import json
from pathlib import Path

from content_studio import paths
from content_studio.db import jobs as jobs_store
from content_studio.db import schema
from content_studio.db.connection import connect
from content_studio.editor.project import validate

TURNS = {
    'duration': 4.0,
    'speakers': ['SPEAKER_00', 'SPEAKER_01'],
    'diarization': [
        {'start': 0.0, 'end': 1.2, 'speaker': 'SPEAKER_00'},
        {'start': 1.0, 'end': 3.0, 'speaker': 'SPEAKER_01'},
    ],
    'exclusive_diarization': [
        {'start': 0.0, 'end': 1.0, 'speaker': 'SPEAKER_00'},
        {'start': 1.0, 'end': 3.0, 'speaker': 'SPEAKER_01'},
    ],
}
SPEAKERS = {
    'SPEAKER_00': {'name': 'Hablante 1', 'color': '#2563eb'},
    'SPEAKER_01': {'name': 'Hablante 2', 'color': '#dc2626'},
}


def _job(api, kind: str = 'diarize', wavs: bool = True) -> int:
    """Un trabajo terminado con sus archivos de turnos; con `wavs`, un `diarize.split` que separó los audios."""
    folder = api.tmp / 'out' / f'{kind}-job'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'turns.json').write_text(json.dumps(TURNS), encoding='utf-8')
    (folder / 'turns.rttm').write_text('SPEAKER audio 1 0.000 1.000 <NA> <NA> SPEAKER_00 <NA> <NA>\n', encoding='utf-8')
    (folder / 'turns.csv').write_text('start,end,speaker,name\n0.000,1.000,SPEAKER_00,Hablante 1\n', encoding='utf-8')
    (folder / 'speakers.json').write_text(json.dumps(SPEAKERS), encoding='utf-8')
    conn = connect(api.tmp / 'base.db')
    try:
        schema.migrate(conn)
        job_id = jobs_store.insert(conn, kind, 'gpu', {'input': 'C:/in/charla.wav'})
        jobs_store.update(conn, job_id, status='done', output_dir=str(folder))
        if wavs:
            split = api.tmp / 'out' / 'split-job'
            (split / 'speakers').mkdir(parents=True)
            for speaker in ('SPEAKER_00', 'SPEAKER_01'):
                (split / 'speakers' / f'{speaker}.wav').write_bytes(b'RIFF')
            split_id = jobs_store.insert(
                conn, 'diarize.split', 'cpu', {'input': 'C:/in/charla.wav', 'turns': str(folder)}
            )
            jobs_store.update(conn, split_id, status='done', output_dir=str(split))
        conn.commit()
    finally:
        conn.close()
    return job_id


def test_ac4_result_and_files(api):
    """AC-4: GET entrega turnos, hablantes, rutas de los archivos y los WAV por hablante."""
    job_id = _job(api)

    got = api.client.get(f'/diarizations/{job_id}', headers=api.headers)

    assert got.status_code == 200
    body = got.json()
    assert body['source'] == 'C:/in/charla.wav'
    assert body['duration'] == 4.0
    assert body['turns'] == TURNS['diarization']
    assert body['exclusive_turns'] == TURNS['exclusive_diarization']
    assert body['speakers'] == SPEAKERS
    assert set(body['files']) == {'json', 'rttm', 'csv'}
    assert body['files']['csv'].endswith('turns.csv')
    assert set(body['split']) == {'SPEAKER_00', 'SPEAKER_01'}
    assert body['split']['SPEAKER_00'].endswith('SPEAKER_00.wav')


def test_ac4_without_wav_split_is_null(api):
    """AC-4: sin WAV por hablante, split es null: la sección ofrece «Un audio por hablante»."""
    job_id = _job(api, wavs=False)

    assert api.client.get(f'/diarizations/{job_id}', headers=api.headers).json()['split'] is None


def test_ac4_other_job_answers_409(api):
    """AC-4: un trabajo que no es diarize no tiene resultado de diarización: 409 not_a_diarization."""
    job_id = _job(api, kind='transcribe')

    got = api.client.get(f'/diarizations/{job_id}', headers=api.headers)

    assert got.status_code == 409
    assert 'not_a_diarization' in got.text


def test_ac4_unknown_job_answers_404(api):
    """AC-4: un id que no existe responde 404."""
    assert api.client.get('/diarizations/999', headers=api.headers).status_code == 404


def test_ac6_the_route_creates_the_project(api, monkeypatch, tmp_path):
    """AC-6: POST crea un proyecto del Editor con el audio y un marcador por turno; devuelve su project.json."""
    monkeypatch.setattr(paths, 'outputs_dir', lambda: tmp_path / 'outputs')
    job_id = _job(api)

    created = api.client.post('/editor/projects/from-diarization', json={'job': job_id}, headers=api.headers)

    assert created.status_code == 201
    project = Path(created.json()['project'])
    assert project.name == 'project.json'
    doc = json.loads(project.read_text(encoding='utf-8'))
    assert [(marker['t'], marker['label']) for marker in doc['markers']] == [(0.0, 'Hablante 1'), (1.0, 'Hablante 2')]
    assert validate(doc) == []
