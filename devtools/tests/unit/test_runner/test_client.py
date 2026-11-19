"""Etapas `client-*` del test-runner (spec 005, D-9): corren un script de client/ con bun y mapean su exit code."""

from __future__ import annotations

import subprocess

import pytest

from devtools.test_runner import client


class _Done:
    def __init__(self, returncode: int, stdout: str = '', stderr: str = '') -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.mark.parametrize(
    ('run', 'script', 'stage'),
    [
        (client.lint, 'lint', 'client-lint'),
        (client.unit, 'test', 'client-unit'),
    ],
)
def test_stage_runs_the_client_script_with_bun(monkeypatch, tmp_path, run, script, stage):
    calls = []

    def fake(command, **kwargs):
        calls.append((command, kwargs['cwd']))
        return _Done(0)

    monkeypatch.setattr(subprocess, 'run', fake)

    result = run([], root=tmp_path)

    assert calls == [(['bun', 'run', script], tmp_path / 'client')]
    assert result == {'stage': stage, 'status': 'pass', 'detail': ''}


def test_tauri_check_runs_cargo_check_on_the_tauri_crate(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: calls.append(command) or _Done(0))

    result = client.tauri_check([], root=tmp_path)

    assert calls == [['cargo', 'check', '--manifest-path', str(tmp_path / 'client' / 'src-tauri' / 'Cargo.toml')]]
    assert result == {'stage': 'tauri-check', 'status': 'pass', 'detail': ''}


def test_typecheck_regenerates_the_schema_then_runs_tsc(monkeypatch, tmp_path):
    calls = []

    def fake(command, **kwargs):
        calls.append((command, kwargs['cwd']))
        return _Done(0)

    monkeypatch.setattr(subprocess, 'run', fake)

    result = client.typecheck([], root=tmp_path)

    assert calls == [
        (['bun', 'run', 'gen:api'], tmp_path / 'client'),
        (['git', 'diff', '--quiet', '--', client.SCHEMA], tmp_path),
        (['bun', 'run', 'typecheck'], tmp_path / 'client'),
    ]
    assert result == {'stage': 'client-typecheck', 'status': 'pass', 'detail': ''}


def test_typecheck_fails_when_the_schema_no_longer_matches_openapi(monkeypatch, tmp_path):
    calls = []

    def fake(command, **kwargs):
        calls.append(command)
        return _Done(1 if command[:2] == ['git', 'diff'] else 0)

    monkeypatch.setattr(subprocess, 'run', fake)

    result = client.typecheck([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'schema.d.ts' in result['detail']
    assert ['bun', 'run', 'typecheck'] not in calls


def test_failing_tsc_fails_the_stage_and_keeps_its_output(monkeypatch, tmp_path):
    def fake(command, **kwargs):
        return _Done(1, stdout='error TS2322', stderr='') if 'typecheck' in command else _Done(0)

    monkeypatch.setattr(subprocess, 'run', fake)

    result = client.typecheck([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'TS2322' in result['detail']


def test_e2e_runs_the_playwright_workspace(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: calls.append((command, kwargs['cwd'])) or _Done(0))

    result = client.e2e([], root=tmp_path)

    assert calls == [(['bun', 'run', 'test'], tmp_path / 'tests' / 'e2e')]
    assert result == {'stage': 'e2e', 'status': 'pass', 'detail': ''}


def test_a_missing_tool_fails_the_stage_and_names_it(monkeypatch, tmp_path):
    def missing(*args, **kwargs):
        raise FileNotFoundError('bun')

    monkeypatch.setattr(subprocess, 'run', missing)

    result = client.lint([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'bun is not in PATH' in result['detail']
