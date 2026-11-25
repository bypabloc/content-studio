"""Rutas de hablantes (spec 036, D-2): el texto de un trabajo, sus nombres y colores, y el TXT (AC-5 y AC-6)."""

from __future__ import annotations

import json
from pathlib import Path

from content_studio.db import jobs as jobs_store
from content_studio.db import schema
from content_studio.db.connection import connect

WORDS = {
    'language': 'es',
    'language_probability': 0.99,
    'duration': 4.0,
    'text': 'hola mundo',
    'segments': [
        {
            'start': 0.0,
            'end': 1.0,
            'text': 'hola',
            'speaker': 'SPEAKER_00',
            'words': [{'start': 0.0, 'end': 1.0, 'word': ' hola', 'probability': 0.9, 'speaker': 'SPEAKER_00'}],
        },
        {
            'start': 2.5,
            'end': 3.0,
            'text': 'mundo',
            'speaker': 'SPEAKER_01',
            'words': [{'start': 2.5, 'end': 3.0, 'word': ' mundo', 'probability': 0.9, 'speaker': 'SPEAKER_01'}],
        },
    ],
}
SPEAKERS = {
    'SPEAKER_00': {'name': 'Hablante 1', 'color': '#2563eb'},
    'SPEAKER_01': {'name': 'Hablante 2', 'color': '#dc2626'},
}
TURNS = {
    'duration': 4.0,
    'speakers': ['SPEAKER_00', 'SPEAKER_01'],
    'diarization': [],
    'exclusive_diarization': [
        {'start': 0.0, 'end': 1.0, 'speaker': 'SPEAKER_00'},
        {'start': 2.5, 'end': 3.0, 'speaker': 'SPEAKER_01'},
    ],
}


def _job(api, turns: bool = True) -> tuple[int, Path]:
    """Un trabajo transcribe terminado con words.json, speakers.json y, si se pide, turns.json y turns.csv."""
    folder = api.tmp / 'out' / 'transcribe-job'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'words.json').write_text(json.dumps(WORDS), encoding='utf-8')
    (folder / 'speakers.json').write_text(json.dumps(SPEAKERS), encoding='utf-8')
    if turns:
        (folder / 'turns.json').write_text(json.dumps(TURNS), encoding='utf-8')
        (folder / 'turns.csv').write_text('start,end,speaker,name\n', encoding='utf-8')
    conn = connect(api.tmp / 'base.db')
    try:
        schema.migrate(conn)
        job_id = jobs_store.insert(conn, 'transcribe', 'gpu', {'input': 'a.wav', 'model': 'small', 'diarize': True})
        jobs_store.update(conn, job_id, status='done', output_dir=str(folder))
        conn.commit()
    finally:
        conn.close()
    return job_id, folder


def test_ac5_get_put_validates_the_input(api):
    """AC-5: GET une words.json y speakers.json; PUT guarda y responde lo guardado.

    Un nombre de 41 caracteres, un color que no es hex o un id desconocido dan 422; turns.csv se regenera.
    """
    job_id, folder = _job(api)

    got = api.client.get(f'/jobs/{job_id}/transcript', headers=api.headers)
    assert got.status_code == 200
    assert got.json()['speakers']['SPEAKER_01']['name'] == 'Hablante 2'
    assert got.json()['segments'][1]['speaker'] == 'SPEAKER_01'

    renamed = {
        'SPEAKER_00': {'name': 'Ana', 'color': '#16a34a'},
        'SPEAKER_01': {'name': 'Luis', 'color': '#dc2626'},
    }
    saved = api.client.put(f'/jobs/{job_id}/speakers', json=renamed, headers=api.headers)
    assert saved.status_code == 200
    assert saved.json() == renamed
    assert json.loads((folder / 'speakers.json').read_text(encoding='utf-8'))['SPEAKER_00']['name'] == 'Ana'
    assert 'Ana' in (folder / 'turns.csv').read_text(encoding='utf-8')

    too_long = {'SPEAKER_00': {'name': 'x' * 41, 'color': '#16a34a'}}
    assert api.client.put(f'/jobs/{job_id}/speakers', json=too_long, headers=api.headers).status_code == 422
    empty = {'SPEAKER_00': {'name': '  ', 'color': '#16a34a'}}
    assert api.client.put(f'/jobs/{job_id}/speakers', json=empty, headers=api.headers).status_code == 422
    not_hex = {'SPEAKER_00': {'name': 'Ana', 'color': 'red'}}
    assert api.client.put(f'/jobs/{job_id}/speakers', json=not_hex, headers=api.headers).status_code == 422
    unknown = {'SPEAKER_09': {'name': 'Ana', 'color': '#16a34a'}}
    assert api.client.put(f'/jobs/{job_id}/speakers', json=unknown, headers=api.headers).status_code == 422


def test_ac6_export_writes_the_file(api):
    """AC-6: el TXT queda en la carpeta del trabajo con los nombres actuales, con o sin marcas de tiempo."""
    job_id, folder = _job(api)

    with_time = api.client.post(f'/jobs/{job_id}/transcript/export', json={'timestamps': True}, headers=api.headers)
    assert with_time.status_code == 200
    assert Path(with_time.json()['path']) == folder / 'transcript.txt'
    assert (folder / 'transcript.txt').read_text(encoding='utf-8') == (
        '[00:00:00] Hablante 1: hola\n[00:00:02] Hablante 2: mundo\n'
    )

    api.client.post(f'/jobs/{job_id}/transcript/export', json={'timestamps': False}, headers=api.headers)
    assert (folder / 'transcript.txt').read_text(encoding='utf-8') == 'Hablante 1: hola\nHablante 2: mundo\n'
