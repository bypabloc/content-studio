"""CLI `studio` (spec 004, D-6, AC-9): ayuda, exit 2 con argumentos malos y nada que pregunte sin TTY."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.cli.main import main
from content_studio.db import connection, jobs, schema


@pytest.fixture
def db(tmp_path) -> str:
    path = tmp_path / 'base.db'
    conn = connection.connect(path)
    schema.migrate(conn)
    conn.close()
    return str(path)


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
