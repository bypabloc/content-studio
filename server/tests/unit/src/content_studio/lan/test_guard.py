"""Spec 032, AC-6: desde la red local las entradas son subidas propias; ninguna ruta de esta PC ni tipo de admin."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

import pytest

from content_studio.api.errors import ApiError
from content_studio.db import connection, schema
from content_studio.lan import clients, guard


@pytest.fixture
def conn(tmp_path):
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        yield conn


def _refused(conn, client_id: int, kind: str, params: dict) -> tuple[int, str]:
    with pytest.raises(ApiError) as caught:
        guard.remote_params(conn, client_id, kind, params)
    return caught.value.status_code, caught.value.code


def test_ac6_upload_yes_path_no(conn, tmp_path):
    owner, _ = clients.create(conn, 'celular')
    upload = guard.record_upload(conn, owner, tmp_path / 'a.wav', 3)

    params = guard.remote_params(conn, owner, 'media.convert', {'input': f'upload:{upload}', 'target': 'mp3'})

    assert params == {'input': str(tmp_path / 'a.wav'), 'target': 'mp3'}
    assert _refused(conn, owner, 'media.convert', {'input': 'C:/Users/x/a.wav'}) == (403, 'remote_path_not_allowed')
    assert _refused(conn, owner, 'engine.install', {'engine': 'qwen'}) == (403, 'kind_not_allowed_remote')


def test_an_upload_of_another_device_is_not_found(conn, tmp_path):
    owner, _ = clients.create(conn, 'celular')
    other, _ = clients.create(conn, 'tablet')
    upload = guard.record_upload(conn, owner, tmp_path / 'a.wav', 3)

    assert _refused(conn, other, 'media.convert', {'input': f'upload:{upload}'}) == (404, 'upload_not_found')
    assert _refused(conn, other, 'media.convert', {'input': 'upload:nope'}) == (404, 'upload_not_found')


def test_a_script_list_takes_uploads_too(conn, tmp_path):
    owner, _ = clients.create(conn, 'celular')
    upload = guard.record_upload(conn, owner, tmp_path / 'guion.txt', 10)

    params = guard.remote_params(conn, owner, 'narration', {'file': [f'upload:{upload}'], 'style': 'expert'})

    assert params['file'] == [str(tmp_path / 'guion.txt')]


def test_a_path_hidden_in_another_param_is_refused(conn):
    owner, _ = clients.create(conn, 'celular')

    refused = _refused(conn, owner, 'media.convert', {'input': 'upload:1', 'options': {'x': r'\\server\share'}})

    assert refused[1] in ('remote_path_not_allowed', 'upload_not_found')
    assert _refused(conn, owner, 'music', {'style': ['lofi'], 'out': '/etc/passwd'}) == (403, 'remote_path_not_allowed')


def test_plain_text_passes(conn):
    owner, _ = clients.create(conn, 'celular')

    params = guard.remote_params(conn, owner, 'narration', {'text': 'Hola, mundo. 1/2 kilo.', 'style': 'expert'})

    assert params == {'text': 'Hola, mundo. 1/2 kilo.', 'style': 'expert'}


def test_safe_name_keeps_only_the_file_name():
    assert guard.safe_name('../../a b.wav') == 'a_b.wav'
    assert guard.safe_name('C:\\x\\voz.mp3') == 'voz.mp3'
    assert guard.safe_name('...') == 'upload'
    assert Path(guard.safe_name('ñandú.wav')).suffix == '.wav'
