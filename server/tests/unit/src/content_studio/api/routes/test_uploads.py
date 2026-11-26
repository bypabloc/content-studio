"""Spec 032, AC-6: un dispositivo sube un archivo, lo usa como entrada de un trabajo y el tope da 413."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from content_studio.api.app import create_app
from content_studio.db import connection
from content_studio.db import jobs as store
from content_studio.lan import clients


@pytest.fixture
def lan(tmp_path, monkeypatch):
    monkeypatch.setattr('content_studio.paths.outputs_dir', lambda database=None: tmp_path / 'out')
    db = tmp_path / 'base.db'
    app = create_app(db, 'local-token', remote=True, max_upload_mb=1)
    with closing(connection.connect(db)) as conn:
        client_id, token = clients.create(conn, 'celular')
    return SimpleNamespace(
        db=db, tmp=tmp_path, client=TestClient(app), id=client_id, headers={'Authorization': f'Bearer {token}'}
    )


def test_ac6_upload_then_convert_uses_the_upload(lan):
    uploaded = lan.client.post('/uploads', params={'name': 'voz.wav'}, content=b'RIFF', headers=lan.headers).json()

    job = {'kind': 'media.convert', 'params': {'input': uploaded['ref'], 'target': 'mp3'}}

    created = lan.client.post('/jobs', json=job, headers=lan.headers)

    assert uploaded['size'] == 4
    assert created.status_code == 201, created.text
    path = created.json()['params']['input']
    assert path.startswith(str(lan.tmp / 'out' / 'uploads' / str(lan.id)))
    assert Path(path).read_bytes() == b'RIFF'
    with closing(connection.connect(lan.db)) as conn:
        assert store.get(conn, created.json()['id'])['client_id'] == lan.id


def test_ac6_a_path_of_this_pc_is_403(lan):
    job = {'kind': 'media.convert', 'params': {'input': 'C:/Windows/win.ini', 'target': 'mp3'}}

    response = lan.client.post('/jobs', json=job, headers=lan.headers)

    assert response.status_code == 403
    assert response.json()['code'] == 'remote_path_not_allowed'


def test_ac6_an_admin_kind_is_403(lan):
    response = lan.client.post('/jobs', json={'kind': 'engine.install', 'params': {}}, headers=lan.headers)

    assert response.status_code == 403
    assert response.json()['code'] == 'kind_not_allowed_remote'


def test_ac6_a_file_over_the_limit_is_413_and_not_kept(lan):
    body = b'x' * (1024 * 1024 + 1)

    response = lan.client.post('/uploads', params={'name': 'big.wav'}, content=body, headers=lan.headers)

    assert response.status_code == 413
    assert response.json()['code'] == 'upload_too_large'
    assert not any((lan.tmp / 'out' / 'uploads').rglob('*.wav'))


def test_an_invalid_job_is_422(lan):
    uploaded = lan.client.post('/uploads', params={'name': 'a.wav'}, content=b'1', headers=lan.headers).json()

    job = {'kind': 'media.convert', 'params': {'input': uploaded['ref']}}

    response = lan.client.post('/jobs', json=job, headers=lan.headers)

    assert response.status_code == 422


def test_uploads_need_the_device_token(lan):
    assert lan.client.post('/uploads', params={'name': 'a.wav'}, content=b'1').status_code == 401
