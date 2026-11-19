"""CLI `studio` (spec 004, D-6, AC-9): ayuda, exit 2 con argumentos malos y nada que pregunte sin TTY."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

import content_studio.cli.main as cli_main
from content_studio.cli import serve, submit
from content_studio.cli.main import main
from content_studio.db import connection, jobs, schema


@pytest.fixture
def db(tmp_path) -> str:
    path = tmp_path / 'base.db'
    conn = connection.connect(path)
    schema.migrate(conn)
    conn.close()
    return str(path)


@pytest.fixture
def checkout(monkeypatch, tmp_path):
    monkeypatch.setattr(cli_main, 'main_checkout', lambda start: tmp_path)
    return tmp_path


def test_help_lists_the_subcommands(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['--help'])

    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert all(word in out for word in ('serve', 'narration', 'music', 'jobs'))


def test_ac9_an_unknown_music_model_exits_2(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['music', '--model', 'foo'])

    assert exit_info.value.code == 2


def test_ac9_the_tts_help_shows_its_flags(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['narration', 'tts', '--help'])

    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert '--model' in out and '--style' in out


def test_nothing_is_asked_without_a_tty(db, monkeypatch):
    def no_prompts(*args, **kwargs):
        raise AssertionError('studio no debe preguntar nada')

    monkeypatch.setattr('builtins.input', no_prompts)

    assert main(['--db', db, 'jobs', 'list']) == 0


def test_jobs_cancel_marks_a_queued_job_and_list_shows_it(db, capsys):
    conn = connection.connect(Path(db))
    job_id = jobs.insert(conn, 'fake', 'gpu', {})
    conn.close()

    assert main(['--db', db, 'jobs', 'cancel', str(job_id)]) == 0
    capsys.readouterr()
    assert main(['--db', db, 'jobs', 'list']) == 0

    listed = json.loads(capsys.readouterr().out)
    assert [(job['id'], job['status']) for job in listed] == [(job_id, 'cancelled')]


def test_cancelling_a_missing_job_exits_1(db):
    assert main(['--db', db, 'jobs', 'cancel', '999']) == 1


def test_retry_of_a_job_still_queued_exits_1(db, capsys):
    conn = connection.connect(Path(db))
    job_id = jobs.insert(conn, 'fake', 'gpu', {})
    conn.close()

    assert main(['--db', db, 'jobs', 'retry', str(job_id)]) == 1
    assert 'not finished' in capsys.readouterr().err


def test_retry_of_a_finished_job_queues_a_copy(db, capsys):
    conn = connection.connect(Path(db))
    job_id = jobs.insert(conn, 'fake', 'gpu', {'a': 1})
    conn.execute("UPDATE jobs SET status = 'error' WHERE id = ?", (job_id,))
    conn.close()
    capsys.readouterr()

    assert main(['--db', db, 'jobs', 'retry', str(job_id)]) == 0
    assert json.loads(capsys.readouterr().out)['job'] != job_id


def test_narration_voices_runs_the_voices_tool_under_the_gpu_lock(monkeypatch, checkout):
    calls = []
    monkeypatch.setattr(cli_main.gpu_lock, 'acquire', lambda main_dir, job, command, wait: calls.append(job) or True)
    monkeypatch.setattr(cli_main.gpu_lock, 'release', lambda main_dir: calls.append('release'))
    monkeypatch.setattr(cli_main, 'subprocess', types.SimpleNamespace(call=lambda cmd: calls.append(cmd) or 0))

    assert main(['narration', 'voices', '--list']) == 0

    expected_cmd = [sys.executable, '-m', 'content_studio.narration.voices.main', '--list']
    assert calls == ['narration-voices', expected_cmd, 'release']


def test_serve_passes_its_flags_to_the_server(monkeypatch, checkout):
    seen = {}
    monkeypatch.setattr(serve, 'serve', lambda db, root, port, token: seen.update(port=port, token=token) or 0)

    assert main(['serve', '--port', '9', '--token', 'abc']) == 0
    assert seen == {'port': 9, 'token': 'abc'}


def test_narration_tts_and_music_go_to_submit(monkeypatch, checkout):
    sent = []
    monkeypatch.setattr(submit, 'run', lambda kind, params, db, root: sent.append((kind, params)) or 0)

    assert main(['narration', 'tts', '--model', 'qwen-0.6b', '--style', 'expert', '--text', 'Hola.']) == 0
    assert main(['music', '--model', 'acestep', '--style', 'lofi-chill', '--duration', '15']) == 0
    assert [kind for kind, _ in sent] == ['narration', 'music']


def test_output_flag_exits_2_and_says_why(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['narration', 'tts', '--model', 'qwen-0.6b', '--style', 'expert', '--text', 'x', '--output', 'y.wav'])

    assert exit_info.value.code == 2
    assert 'drop --output' in capsys.readouterr().err


def test_an_unknown_flag_exits_2_on_every_command_but_voices(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['music', '--model', 'acestep', '--bogus'])

    assert exit_info.value.code == 2
    assert 'unrecognized arguments: --bogus' in capsys.readouterr().err
