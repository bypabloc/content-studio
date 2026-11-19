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
        (client.typecheck, 'typecheck', 'client-typecheck'),
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


def test_failing_script_fails_the_stage_and_keeps_its_output(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: _Done(1, stdout='error TS2322', stderr=''))

    result = client.typecheck([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'TS2322' in result['detail']


def test_e2e_runs_the_playwright_workspace(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: calls.append((command, kwargs['cwd'])) or _Done(0))

    result = client.e2e([], root=tmp_path)

    assert calls == [(['bun', 'run', 'test'], tmp_path / 'tests' / 'e2e')]
    assert result == {'stage': 'e2e', 'status': 'pass', 'detail': ''}
