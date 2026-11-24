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
from content_studio.transcription import models


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
    assert all(word in out for word in ('serve', 'narration', 'music', 'jobs', 'engines'))


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


def test_music_samples_goes_to_submit_without_a_model(monkeypatch, checkout):
    sent = []
    monkeypatch.setattr(submit, 'run', lambda kind, params, db, root: sent.append((kind, params)) or 0)

    assert main(['music', 'samples', '--styles', 'lofi-chill', 'corporate', '--force']) == 0
    assert sent == [('music.samples', {'styles': ['lofi-chill', 'corporate'], 'force': True})]


def test_music_without_a_model_exits_2_and_says_why(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['music', '--style', 'lofi-chill'])

    assert exit_info.value.code == 2
    assert '--model' in capsys.readouterr().err


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


def test_openapi_prints_the_schema_of_the_api(capsys):
    assert main(['openapi']) == 0

    schema = json.loads(capsys.readouterr().out)

    assert {'/jobs', '/jobs/{job_id}', '/queue', '/events', '/settings/{key}'} <= set(schema['paths'])
    assert {'Job', 'QueueState', 'SettingOut'} <= set(schema['components']['schemas'])


def test_openapi_job_schema_lists_the_fields_the_client_shows(capsys):
    main(['openapi'])

    job = json.loads(capsys.readouterr().out)['components']['schemas']['Job']

    assert {'id', 'kind', 'status', 'progress', 'stage', 'error_code', 'params'} <= set(job['properties'])


def test_db_is_accepted_after_the_subcommand(db, capsys):
    assert main(['jobs', 'list', '--db', db]) == 0
    assert main(['--db', db, 'jobs', 'list']) == 0


def test_engines_verify_runs_the_gpu_service(monkeypatch, db, checkout):
    sent = []
    monkeypatch.setattr(submit, 'run', lambda kind, params, database, root: sent.append((kind, params)) or 0)

    assert main(['--db', db, 'engines', 'verify', 'qwen-0.6b']) == 0

    assert sent == [('engine.verify', {'engine': 'qwen-0.6b'})]


def test_engines_actions_use_the_matching_services(monkeypatch, db, checkout):
    sent = []
    monkeypatch.setattr(submit, 'run', lambda kind, params, database, root: sent.append((kind, params)) or 0)

    assert main(['engines', 'install', 'qwen-0.6b', '--db', db]) == 0
    assert main(['engines', 'repair', 'qwen-0.6b', '--db', db]) == 0
    assert main(['engines', 'uninstall', 'qwen-0.6b', '--force', '--db', db]) == 0

    assert sent == [
        ('engine.install', {'engine': 'qwen-0.6b', 'repair': False}),
        ('engine.install', {'engine': 'qwen-0.6b', 'repair': True}),
        ('engine.uninstall', {'engine': 'qwen-0.6b', 'force': True}),
    ]


def test_engines_list_prints_the_catalog(monkeypatch, db, capsys):
    monkeypatch.setattr(cli_main.installer, 'list_engines', lambda conn, root: [{'engine': 'qwen-0.6b'}])

    assert main(['engines', 'list', '--db', db]) == 0

    assert json.loads(capsys.readouterr().out) == [{'engine': 'qwen-0.6b'}]


# `studio clean` (spec 013, D-2 y D-4): valida los medios antes de encolar y, con `--auto`, renderiza el análisis.


def _fake_clean_jobs(monkeypatch, status: str = 'done') -> list[tuple[str, dict]]:
    """Reemplaza el encolado de `studio clean`: anota cada trabajo que pide, sin correr motores."""
    requested: list[tuple[str, dict]] = []

    def execute(kind, params, db, main_folder):
        requested.append((kind, params))
        return {'job': len(requested), 'status': status, 'output_dir': f'out/analysis-{len(requested)}'}

    def run(kind, params, db, main_folder):
        requested.append((kind, params))
        return 0

    monkeypatch.setattr(submit, 'execute', execute)
    monkeypatch.setattr(submit, 'run', run)
    monkeypatch.setattr(cli_main, 'main_checkout', lambda start: Path('.'))
    return requested


def test_clean_help_shows_the_auto_flag(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['clean', '--help'])

    assert exit_info.value.code == 0
    assert '--auto' in capsys.readouterr().out


def test_clean_analyzes_with_the_recommended_model_by_default(tmp_path, db, monkeypatch):
    media = tmp_path / 'charla.mp4'
    media.write_bytes(b'')  # `studio clean` solo mira que exista y su extensión: el análisis no corre aquí
    requested = _fake_clean_jobs(monkeypatch)

    assert main(['clean', str(media), '--db', db]) == 0

    assert requested == [
        (
            'clean.analyze',
            {
                'input': str(media),
                'model': models.recommended(),
                'language': 'auto',
                'min_gap': 0.5,
                'padding': 0.15,
                'edges': True,
            },
        )
    ]


def test_clean_without_auto_only_analyzes(tmp_path, db, monkeypatch):
    media = tmp_path / 'charla.mp4'
    media.write_bytes(b'')
    requested = _fake_clean_jobs(monkeypatch)

    main(['clean', str(media), '--db', db])

    assert [kind for kind, _ in requested] == ['clean.analyze']


def test_clean_auto_renders_the_analysis_folder(tmp_path, db, monkeypatch):
    media = tmp_path / 'charla.mp4'
    media.write_bytes(b'')
    requested = _fake_clean_jobs(monkeypatch)

    assert main(['clean', str(media), '--auto', '--db', db]) == 0

    assert requested[1] == ('clean.render', {'input': str(media), 'analysis': 'out/analysis-1'})


def test_clean_no_edges_turns_off_the_edge_cuts(tmp_path, db, monkeypatch):
    media = tmp_path / 'charla.mp4'
    media.write_bytes(b'')
    requested = _fake_clean_jobs(monkeypatch)

    main(['clean', str(media), '--no-edges', '--db', db])

    assert requested[0][1]['edges'] is False


def test_clean_failed_analysis_is_not_rendered(tmp_path, db, monkeypatch):
    media = tmp_path / 'charla.mp4'
    media.write_bytes(b'')
    requested = _fake_clean_jobs(monkeypatch, status='error')

    assert main(['clean', str(media), '--auto', '--db', db]) == 1

    assert [kind for kind, _ in requested] == ['clean.analyze']


def test_clean_missing_file_exits_2_before_queueing(tmp_path, db, monkeypatch, capsys):
    requested = _fake_clean_jobs(monkeypatch)
    missing = tmp_path / 'no-existe.mp4'

    assert main(['clean', str(missing), '--db', db]) == 2

    assert requested == []
    assert 'no-existe.mp4' in capsys.readouterr().err


def test_clean_unsupported_format_exits_2_before_queueing(tmp_path, db, monkeypatch, capsys):
    requested = _fake_clean_jobs(monkeypatch)
    notes = tmp_path / 'notas.txt'
    notes.write_text('no es audio', encoding='utf-8')

    assert main(['clean', str(notes), '--db', db]) == 2

    assert requested == []
    assert 'notas.txt' in capsys.readouterr().err
