"""Spec 032: rutas de la app de la red local (create_app(remote=True)): emparejar, token por dispositivo y lo propio."""

from __future__ import annotations

from contextlib import closing
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from content_studio.api.app import create_app
from content_studio.db import connection
from content_studio.db import jobs as store
from content_studio.lan import cert, clients
from content_studio.lan.pairing import MAX_FAILURES, Pairing


@pytest.fixture
def lan(tmp_path):
    db = tmp_path / 'base.db'
    cert_path, _ = cert.ensure(tmp_path, '127.0.0.2')
    pairing = Pairing()
    app = create_app(db, 'local-token', remote=True, pairing=pairing, cert_path=cert_path)
    with closing(connection.connect(db)) as conn:
        first_id, first = clients.create(conn, 'celular')
        second_id, second = clients.create(conn, 'tablet')
    return SimpleNamespace(
        db=db,
        tmp=tmp_path,
        app=app,
        client=TestClient(app),
        pairing=pairing,
        cert_path=cert_path,
        first=(first_id, {'Authorization': f'Bearer {first}'}),
        second=(second_id, {'Authorization': f'Bearer {second}'}),
    )


def _job(lan, owner: int, output: str | None = None) -> int:
    with closing(connection.connect(lan.db)) as conn:
        job_id = store.insert(conn, 'media.convert', 'cpu', {'input': 'x'})
        store.update(conn, job_id, client_id=owner, output_dir=output)
    return job_id


def test_pair_gives_a_token_and_the_fingerprint_once(lan):
    pin = lan.pairing.new()['pin']

    body = lan.client.post('/pair', json={'pin': pin, 'name': 'otra pc'}).json()
    again = lan.client.post('/pair', json={'pin': pin, 'name': 'otra pc'})

    assert body['fingerprint'] == cert.fingerprint(lan.cert_path)
    assert lan.client.get('/health', headers={'Authorization': f'Bearer {body["token"]}'}).status_code == 200
    assert again.status_code == 401
    assert again.json()['code'] == 'pairing_invalid'


def test_pair_is_locked_after_too_many_failures(lan):
    lan.pairing.new()
    for _ in range(MAX_FAILURES - 1):
        lan.client.post('/pair', json={'pin': 'x', 'name': 'n'})

    response = lan.client.post('/pair', json={'pin': 'x', 'name': 'n'})

    assert response.status_code == 429
    assert response.json()['code'] == 'pairing_locked'


def test_ac4_local_token_or_none_is_401(lan):
    assert lan.client.get('/health').status_code == 401
    assert lan.client.get('/health', headers={'Authorization': 'Bearer local-token'}).status_code == 401
    assert lan.client.get('/health', headers=lan.first[1]).status_code == 200


def test_a_device_without_the_scope_gets_403(lan):
    with closing(connection.connect(lan.db)) as conn:
        _, token = clients.create(conn, 'solo trabajos', scopes=('jobs',))

    response = lan.client.get('/files', params={'path': 'x'}, headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 403
    assert response.json()['code'] == 'scope_not_allowed'


def test_ac7_jobs_are_only_the_device_own(lan):
    mine = _job(lan, lan.first[0])
    theirs = _job(lan, lan.second[0])

    listed = lan.client.get('/jobs', headers=lan.first[1]).json()

    assert [job['id'] for job in listed] == [mine]
    assert lan.client.get(f'/jobs/{mine}', headers=lan.first[1]).status_code == 200
    assert lan.client.get(f'/jobs/{theirs}', headers=lan.first[1]).status_code == 404
    assert lan.client.post(f'/jobs/{theirs}/cancel', headers=lan.first[1]).status_code == 404
    assert lan.client.post(f'/jobs/{mine}/cancel', headers=lan.first[1]).json() == {'cancelled': True}


def test_ac7_files_are_only_the_device_outputs(lan):
    folder = lan.tmp / 'out' / 'media' / 'job'
    folder.mkdir(parents=True)
    (folder / 'a.mp3').write_bytes(b'mp3')
    mine = _job(lan, lan.first[0], str(folder))

    outputs = lan.client.get(f'/jobs/{mine}/outputs', headers=lan.first[1]).json()
    own = lan.client.get('/files', params={'path': outputs[0]}, headers=lan.first[1])
    other = lan.client.get('/files', params={'path': outputs[0]}, headers=lan.second[1])
    missing = lan.client.get('/files', params={'path': str(folder / 'b.mp3')}, headers=lan.first[1])

    assert own.content == b'mp3'
    assert other.status_code == 404
    assert missing.status_code == 404


def test_catalog_and_profiles_are_readable(lan):
    assert 'engines' in lan.client.get('/catalog/narration', headers=lan.first[1]).json()
    assert isinstance(lan.client.get('/voices/profiles', headers=lan.first[1]).json(), list)
