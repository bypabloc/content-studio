"""Spec 028, AC-6: `studio api down` no detiene un server con trabajos; con --force los cancela y lo detiene."""

import json

from content_studio.cli import api as api_cli
from content_studio.db import connection, jobs, schema
from content_studio.runtime import discovery


def test_ac6_down_respects_running_job(tmp_path):
    db = tmp_path / 'content-studio.db'
    conn = connection.connect(db)
    schema.migrate(conn)
    job = jobs.insert(conn, 'fake', 'gpu', {})
    jobs.update(conn, job, status='running')
    discovery.write(tmp_path, {'url': 'http://127.0.0.1:1', 'port': 1, 'pid': 0, 'version': '0.1.0'})
    stopped: list[object] = []
    assert api_cli.down(db, force=False, stop=stopped.append) == 1
    assert stopped == []
    assert jobs.get(conn, job)['status'] == 'running'
    assert api_cli.down(db, force=True, stop=stopped.append) == 0
    assert stopped == [tmp_path]
    assert jobs.get(conn, job)['status'] == 'cancelled'


def test_status_without_server_exits_1(tmp_path, capsys):
    assert api_cli.status(tmp_path / 'content-studio.db') == 1
    assert json.loads(capsys.readouterr().out) == {'alive': False}


def test_token_prints_the_path_never_the_token(tmp_path, capsys):
    assert api_cli.token(tmp_path / 'content-studio.db') == 0
    printed = capsys.readouterr().out
    assert json.loads(printed)['path'].endswith('api-token')
    assert discovery.token(tmp_path) not in printed


def test_up_prints_the_server_address(tmp_path, monkeypatch, capsys):
    info = {'url': 'http://127.0.0.1:41830', 'port': 41830, 'pid': 1, 'version': '0.1.0'}
    monkeypatch.setattr(api_cli.instance, 'ensure_running', lambda db: info)
    assert api_cli.up(tmp_path / 'content-studio.db') == 0
    assert json.loads(capsys.readouterr().out) == {'ready': info}
