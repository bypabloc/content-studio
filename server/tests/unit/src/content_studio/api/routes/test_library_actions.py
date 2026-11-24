"""Rutas de acciones de la biblioteca (spec 020, D-4, AC-4 y AC-5)."""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

import pytest

from content_studio.db import connection, jobs
from content_studio.library import actions, index


@pytest.fixture
def item(api, monkeypatch):
    """Un ítem de narración con su trabajo, y la papelera y las rutas protegidas simuladas."""
    trashed: list[str] = []
    monkeypatch.setattr(actions, 'send_to_trash', lambda path: trashed.append(Path(path).name) or Path(path).unlink())
    monkeypatch.setattr(actions, 'protected_roots', lambda: [api.tmp / 'reference'])
    folder = api.tmp / 'out' / 'a'
    folder.mkdir(parents=True)
    (folder / 'take.srt').write_text('', encoding='utf-8')
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        job_id = jobs.insert(conn, 'narration', 'gpu', {'text': 'hola'})
        jobs.update(conn, job_id, status='done', output_dir=str(folder), result=json.dumps({}))
        [item_id] = index.register_job(conn, jobs.get(conn, job_id))
    api.trashed = trashed
    return item_id


def test_detail_repeat_rename_move_and_delete(api, item):
    """GET /library/{id}, repetir, renombrar, mover y borrar con `files`."""
    h = api.headers
    dest = api.tmp / 'out' / 'dest'
    dest.mkdir()

    detail = api.client.get(f'/library/{item}', headers=h).json()
    repeated = api.client.post(f'/library/{item}/repeat', headers=h)
    renamed = api.client.post(f'/library/{item}/rename', json={'name': 'final'}, headers=h).json()
    moved = api.client.post(f'/library/{item}/move', json={'folder': str(dest)}, headers=h).json()
    deleted = api.client.post(f'/library/{item}/delete', json={'files': True}, headers=h)

    assert detail['job']['params'] == {'text': 'hola'}
    assert (repeated.status_code, repeated.json()['params']) == (201, {'text': 'hola'})
    assert renamed['name'] == 'final.srt'
    assert Path(moved['path']) == dest / 'final.srt'
    assert (deleted.status_code, deleted.json(), api.trashed) == (200, {'removed': 1}, ['final.srt'])


def test_ac4_rename_onto_an_existing_name_is_409(api, item):
    """AC-4: 409 `path_exists` y nada cambia."""
    (api.tmp / 'out' / 'a' / 'otro.srt').write_text('', encoding='utf-8')

    response = api.client.post(f'/library/{item}/rename', json={'name': 'otro.srt'}, headers=api.headers)

    assert (response.status_code, response.json()['code']) == (409, 'path_exists')
    assert (api.tmp / 'out' / 'a' / 'take.srt').is_file()


def test_ac5_a_reference_is_protected_and_bad_input_is_422(api, item, monkeypatch):
    """AC-5: una ruta protegida da 403 `protected_path`; un nombre o una carpeta que no sirven, 422."""
    monkeypatch.setattr(actions, 'protected_roots', lambda: [api.tmp / 'out'])
    h = api.headers

    protected = api.client.post(f'/library/{item}/delete', json={'files': True}, headers=h)
    bad_name = api.client.post(f'/library/{item}/rename', json={'name': '../x'}, headers=h)
    bad_folder = api.client.post(f'/library/{item}/move', json={'folder': str(api.tmp / 'nada')}, headers=h)
    missing = api.client.get('/library/999', headers=h)

    assert (protected.status_code, protected.json()['code']) == (403, 'protected_path')
    assert (bad_name.status_code, bad_name.json()['code']) == (422, 'invalid_name')
    assert (bad_folder.status_code, bad_folder.json()['code']) == (422, 'invalid_folder')
    assert (missing.status_code, missing.json()['code']) == (404, 'item_not_found')


def test_bulk_trash_reports_the_count_and_a_watched_item_cannot_repeat(api, item):
    """POST /library/trash manda varios a la papelera con una confirmación; repetir sin trabajo da 409 `no_job`."""
    folder = api.tmp / 'videos'
    folder.mkdir()
    (folder / 'b.srt').write_text('', encoding='utf-8')
    api.client.post('/library/folders', json={'path': str(folder)}, headers=api.headers)
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        from content_studio.library import scan

        scan.scan(conn)
        watched = conn.execute("SELECT id FROM library_items WHERE origin = 'watched'").fetchone()[0]

    repeat = api.client.post(f'/library/{watched}/repeat', headers=api.headers)
    bulk = api.client.post('/library/trash', json={'items': [item, watched]}, headers=api.headers)

    assert (repeat.status_code, repeat.json()['code']) == (409, 'no_job')
    assert bulk.json() == {'removed': 2}
    assert sorted(api.trashed) == ['b.srt', 'take.srt']
