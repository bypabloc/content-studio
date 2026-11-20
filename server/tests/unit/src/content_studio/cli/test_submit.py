"""Flags de `studio` a parámetros de un trabajo (spec 004, D-6): los mismos nombres que usa el servicio."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from content_studio.cli import submit
from content_studio.db import connection, schema
from content_studio.music.parser import build_parser as music_parser
from content_studio.narration.parser import build_parser as narration_parser


class _DoneWorker:
    """Un worker que dice que el trabajo terminó, sin correr ningún motor."""

    def __init__(self, db, main, publish) -> None:
        self.publish = publish

    def run_now(self, job_id: int) -> str:
        return 'done'


@pytest.fixture
def db(tmp_path) -> Path:
    path = tmp_path / 'base.db'
    conn = connection.connect(path)
    schema.migrate(conn)
    conn.close()
    return path


def test_narration_flags_become_the_service_params():
    args = narration_parser().parse_args(['--model', 'qwen-0.6b', '--style', 'expert', '--text', 'Hola.'])

    params = submit.narration_params(args)

    assert (params['model'], params['style'], params['text']) == ('qwen-0.6b', 'expert', 'Hola.')
    assert 'evaluate' not in params  # un flag que no se pidió no viaja al trabajo


def test_narration_file_paths_become_strings():
    args = narration_parser().parse_args(['--model', 'qwen-0.6b', '--style', 'expert', '--file', 'guion.txt'])

    assert submit.narration_params(args)['file'] == ['guion.txt']


def test_each_script_of_a_narration_becomes_its_own_job():
    """Cada guion tiene su carpeta (su blocks/ y su script.json): varios --file son varios trabajos, como en la app."""
    args = narration_parser().parse_args(['--model', 'qwen-0.6b', '--style', 'expert', '--file', 'a.txt', 'b.txt'])

    params = submit.split_files(submit.narration_params(args))

    assert [item['file'] for item in params] == [['a.txt'], ['b.txt']]


def test_a_single_script_or_a_text_stays_one_job():
    one = narration_parser().parse_args(['--model', 'qwen-0.6b', '--style', 'expert', '--file', 'a.txt'])
    text = narration_parser().parse_args(['--model', 'qwen-0.6b', '--style', 'expert', '--text', 'Hola.'])

    assert [item['file'] for item in submit.split_files(submit.narration_params(one))] == [['a.txt']]
    assert submit.split_files(submit.narration_params(text)) == [submit.narration_params(text)]


def test_music_keeps_the_style_list_and_the_duration_as_a_number():
    args = music_parser().parse_args(['--model', 'acestep', '--style', 'lofi-chill', 'corporate', '--duration', '15'])

    params = submit.music_params(args)

    assert (params['model'], params['style'], params['duration']) == ('acestep', ['lofi-chill', 'corporate'], 15.0)


def test_output_is_refused_because_the_job_folder_decides_where_it_goes():
    args = narration_parser().parse_args(
        ['--model', 'qwen-0.6b', '--style', 'expert', '--text', 'x', '--output', 'y.wav']
    )

    with pytest.raises(submit.UsageError):
        submit.narration_params(args)


def test_music_folder_is_refused_because_the_job_folder_decides_where_it_goes():
    args = music_parser().parse_args(['--model', 'acestep', '--style', 'lofi-chill', '--folder', 'otra'])

    with pytest.raises(submit.UsageError):
        submit.music_params(args)


def test_show_progress_prints_one_line_per_job_event(capsys):
    submit._show_progress({'type': 'job', 'data': {'id': 7, 'status': 'running', 'progress': 0.5, 'stage': 'tts'}})
    submit._show_progress({'type': 'log', 'data': {}})

    assert capsys.readouterr().err == 'job 7: running 50% tts\n'


def test_run_queues_the_job_runs_it_here_and_prints_the_result(db, monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(submit, 'Worker', _DoneWorker)
    # El servicio real exige el venv del motor (no existe en la CI): aquí se prueba el flujo, no la validación.
    monkeypatch.setitem(submit.SERVICES, 'music', SimpleNamespace(RESOURCE='gpu', validate=lambda params: []))

    code = submit.run('music', {'model': 'acestep', 'style': ['lofi-chill'], 'duration': 15.0}, db, tmp_path)

    assert code == 0
    printed = json.loads(capsys.readouterr().out)
    assert (printed['status'], printed['output_dir']) == ('done', None)


def test_run_exits_2_and_says_why_when_the_parameters_are_invalid(db, capsys, tmp_path):
    assert submit.run('music', {'model': 'foo'}, db, tmp_path) == 2
    assert capsys.readouterr().err


def test_samples_params_carry_only_the_flags_given():
    assert submit.samples_params(SimpleNamespace(styles=['lofi-chill'], force=False)) == {'styles': ['lofi-chill']}
    assert submit.samples_params(SimpleNamespace(styles=None, force=True)) == {'force': True}
