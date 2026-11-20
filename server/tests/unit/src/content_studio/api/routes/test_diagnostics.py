"""Registro de la grabación y del micrófono (spec 010, D-7): cada evento es una línea en logs/recording/<día>.log."""

from __future__ import annotations

import json

import pytest

from content_studio import paths


@pytest.fixture
def logs(tmp_path, monkeypatch):
    folder = tmp_path / 'logs'
    monkeypatch.setattr(paths, 'LOGS', folder)
    return folder


def test_each_event_is_one_line_in_the_day_file(api, logs):
    response = api.client.post(
        '/diagnostics/recording',
        json={'event': 'record.start', 'detail': {'device': 'mic-1'}},
        headers=api.headers,
    )
    api.client.post('/diagnostics/recording', json={'event': 'record.stop'}, headers=api.headers)

    assert response.status_code == 204
    files = list((logs / 'recording').glob('*.log'))
    assert len(files) == 1
    lines = files[0].read_text(encoding='utf-8').splitlines()
    assert [json.loads(line)['event'] for line in lines] == ['record.start', 'record.stop']
    assert json.loads(lines[0])['detail'] == {'device': 'mic-1'}


def test_nothing_is_written_until_an_event_arrives(api, logs):
    assert not (logs / 'recording').exists()


def test_refuses_an_event_name_that_is_not_a_key(api, logs):
    response = api.client.post(
        '/diagnostics/recording',
        json={'event': 'record start\nfake'},
        headers=api.headers,
    )

    assert response.status_code == 422
    assert not (logs / 'recording').exists()
