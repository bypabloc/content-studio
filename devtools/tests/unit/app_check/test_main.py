"""devtools app-check: la CLI, su línea JSON y sus exit codes (spec 024, AC-5 y AC-7)."""

from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest

from devtools.app_check import launch, main


@pytest.fixture
def fake(tmp_path, monkeypatch):
    """Una corrida sin compilar ni abrir nada: cada paso devuelve lo que pide la prueba."""
    state = SimpleNamespace(build=0, binary=True, cdp=True, scenarios=0, started=[])
    monkeypatch.setattr(main, 'ROOT', tmp_path)
    monkeypatch.setattr(main.os, 'name', 'nt')
    monkeypatch.setattr(main, 'commit', lambda root: 'abc123')
    monkeypatch.setattr(launch, 'build', lambda root, env, log: state.build)
    exe = tmp_path / 'tmp/app-check/cargo-target/debug/content-studio.exe'

    def binary(env):
        if state.binary:
            exe.parent.mkdir(parents=True, exist_ok=True)
            exe.write_text('')
        return exe

    monkeypatch.setattr(launch, 'binary', binary)
    monkeypatch.setattr(launch.Job, '_open', lambda self: 'h')
    monkeypatch.setattr(launch.Job, '_close', lambda self: None)
    monkeypatch.setattr(
        launch.Job, 'start', lambda self, cmd, env, log: state.started.append(cmd) or SimpleNamespace(poll=lambda: None)
    )
    monkeypatch.setattr(launch, 'wait_cdp', lambda port, **kw: state.cdp)

    def scenarios(root, port, run_dir, data, names, log):
        (run_dir / 'report.json').write_text(json.dumps({'tests': [{'title': 'smoke', 'status': 'passed'}]}))
        return state.scenarios

    monkeypatch.setattr(launch, 'scenarios', scenarios)
    return state


def line(capsys) -> dict:
    return json.loads(capsys.readouterr().out.strip())


def test_ac7_run_prints_one_json_line(fake, capsys):
    assert main.main(['run']) == 0
    out = line(capsys)
    assert out['commit'] == 'abc123'
    assert out['data'] == 'temp'
    assert out['binary'].endswith('content-studio.exe')
    assert out['scenarios'] == ['smoke']
    assert out['tests'] == [{'title': 'smoke', 'status': 'passed'}]
    assert out['log'].startswith('logs/app-check-')
    assert fake.started and fake.started[0][0].endswith('content-studio.exe')


def test_ac7_a_failing_scenario_is_exit_1(fake, capsys):
    fake.scenarios = 1
    assert main.main(['run', '--scenario=smoke', '--scenario=dialog-pick']) == 1
    assert line(capsys)['scenarios'] == ['smoke', 'dialog-pick']


@pytest.mark.parametrize(
    ('field', 'value', 'error'), [('build', 2, 'build'), ('binary', False, 'binary'), ('cdp', False, 'CDP')]
)
def test_ac5_launch_failures_are_exit_2(fake, capsys, field, value, error):
    setattr(fake, field, value)
    assert main.main(['run']) == 2
    assert error in line(capsys)['error']


def test_ac4_real_without_database_is_exit_2(fake, capsys, monkeypatch):
    monkeypatch.setattr(main, 'user_db', lambda root: main.ROOT / 'missing.db')
    assert main.main(['run', '--data=real']) == 2
    assert 'no database' in line(capsys)['error']


def test_bad_arguments_and_help(fake, capsys):
    with pytest.raises(SystemExit) as bad:
        main.main(['run', '--data=prod'])
    assert bad.value.code == 2
    assert main.main([]) == 2
    with pytest.raises(SystemExit) as shown:
        main.main(['--help'])
    assert shown.value.code == 0


def test_posix_is_exit_2(fake, capsys, monkeypatch):
    monkeypatch.setattr(main.os, 'name', 'posix')
    assert main.main(['run']) == 2
    assert 'Windows' in line(capsys)['error']


def test_interrupt_is_exit_130(fake, capsys, monkeypatch):
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(launch, 'wait_cdp', interrupted)
    assert main.main(['run']) == 130


def test_user_db_prefers_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv('CONTENT_STUDIO_DB', str(tmp_path / 'x.db'))
    assert main.user_db(tmp_path) == tmp_path / 'x.db'
    monkeypatch.delenv('CONTENT_STUDIO_DB')
    assert main.user_db(main.ROOT).name == 'content-studio.db'
    assert os.name in ('nt', 'posix')
