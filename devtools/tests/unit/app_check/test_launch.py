"""devtools app-check: compilar, abrir dentro de un Job y esperar CDP (spec 024, AC-5 y AC-6)."""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

from devtools.app_check import launch


class Clock:
    """Un reloj que avanza solo cuando el código espera."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def pause(self, seconds: float) -> None:
        self.now += seconds


def test_ac5_build_failure_is_reported_with_its_code(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs['cwd'], kwargs['env']['CARGO_TARGET_DIR']))
        return subprocess.CompletedProcess(command, 101)

    monkeypatch.setattr(launch.subprocess, 'run', fake_run)
    log = tmp_path / 'logs/app-check-x.log'
    assert launch.build(tmp_path, {'CARGO_TARGET_DIR': 't'}, log) == 101
    assert calls == [(['bun', 'run', '--cwd', 'client', 'tauri', 'build', '--debug', '--no-bundle'], tmp_path, 't')]
    assert log.is_file()


def test_ac5_binary_lives_in_the_run_target(tmp_path):
    exe = 'content-studio.exe' if os.name == 'nt' else 'content-studio'
    assert launch.binary({'CARGO_TARGET_DIR': str(tmp_path)}) == tmp_path / 'debug' / exe


def test_ac5_cdp_answers(monkeypatch):
    seen = []

    class Answer:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def opener(url, timeout):
        seen.append(url)
        if len(seen) < 3:
            raise urllib.error.URLError('refused')
        return Answer()

    clock = Clock()
    assert launch.wait_cdp(9333, deadline=10, clock=clock, pause=clock.pause, opener=opener)
    assert seen == ['http://127.0.0.1:9333/json/version'] * 3


def test_ac5_cdp_timeout_gives_up_at_the_deadline():
    def opener(url, timeout):
        raise ConnectionRefusedError

    clock = Clock()
    assert not launch.wait_cdp(9333, deadline=5, clock=clock, pause=clock.pause, opener=opener)
    assert clock.now >= 5


def test_ac5_cdp_wait_stops_when_the_app_died():
    clock = Clock()

    def opener(url, timeout):
        raise ConnectionRefusedError

    assert not launch.wait_cdp(9333, deadline=60, clock=clock, pause=clock.pause, opener=opener, alive=lambda: False)
    assert clock.now == 0


@pytest.mark.skipif(os.name != 'nt', reason='Job Objects are Windows only')
def test_ac6_real_job_kills_only_its_tree(tmp_path):
    marker = tmp_path / 'child.pid'
    # El proceso de la corrida crea un hijo y espera: los dos tienen que morir al cerrar el Job.
    code = (
        'import subprocess, sys, pathlib;'
        f'c = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"]);'
        f'pathlib.Path(r"{marker}").write_text(str(c.pid));'
        'c.wait()'
    )
    outsider = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    try:
        with launch.Job() as job:
            proc = job.start([sys.executable, '-c', code], env=dict(os.environ), log=tmp_path / 'run.log')
            launch.wait_for(marker.exists, deadline=20)
            child = int(marker.read_text())
        assert proc.wait(timeout=10) is not None
        assert not launch.process_alive(child)
        assert outsider.poll() is None
    finally:
        outsider.kill()


def test_ac6_job_closes_even_when_the_body_fails(monkeypatch):
    closed = []
    monkeypatch.setattr(launch.Job, '_open', lambda self: 'h')
    monkeypatch.setattr(launch.Job, '_close', lambda self: closed.append(self.handle))
    with pytest.raises(KeyboardInterrupt), launch.Job():
        raise KeyboardInterrupt
    with launch.Job():
        pass
    assert closed == ['h', 'h']


def test_wait_for_true_and_deadline():
    clock = Clock()
    assert launch.wait_for(lambda: True, deadline=1, clock=clock, pause=clock.pause)
    assert not launch.wait_for(lambda: False, deadline=1, clock=clock, pause=clock.pause)


def test_scenarios_run_playwright_with_the_cdp_endpoint(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs['env']))
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(launch.subprocess, 'run', fake_run)
    code = launch.scenarios(tmp_path, 9333, tmp_path / 'run', 'real', ['smoke', 'dialog-pick'], tmp_path / 'x.log')
    assert code == 1
    command, env = calls[0]
    assert command[-2:] == ['app-check/smoke.check.ts', 'app-check/dialog-pick.check.ts']
    assert env['APP_CHECK_CDP'] == 'http://127.0.0.1:9333'
    assert env['APP_CHECK_RUN'] == str(tmp_path / 'run')
    assert env['APP_CHECK_DATA'] == 'real'
    assert Path(sys.executable).exists()
