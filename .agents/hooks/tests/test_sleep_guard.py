"""sleep_guard.py ejecutado de verdad, como lo llaman Claude Code y Codex: JSON por stdin, exit 2 bloquea."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / 'sleep_guard.py'


def run(tool_input: dict) -> subprocess.CompletedProcess:
    payload = json.dumps({'tool_name': 'Bash', 'tool_input': tool_input})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)


@pytest.mark.parametrize(
    ('tool_input', 'code'),
    [
        ({'command': 'sleep 60; tail -c 1500 tmp/x.log'}, 2),  # el caso del lote 001-017
        ({'command': 'until git log -1 | grep -q x; do sleep 5; done'}, 2),
        ({'command': 'sleep 60', 'run_in_background': True}, 0),
        ({'command': 'gh pr checks 61 --watch'}, 0),
        ({'command': 'git commit -m "chore: sleep guard"'}, 0),
    ],
)
def test_blocks_only_a_foreground_sleep(tool_input, code):
    result = run(tool_input)
    assert result.returncode == code
    assert ('run_in_background' in result.stderr) == (code == 2)


def test_bad_input_does_not_block():
    assert subprocess.run([sys.executable, str(HOOK)], input='no json', capture_output=True, text=True).returncode == 0


def test_antigravity_gets_a_json_deny_on_stdout():
    event = {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'sleep 60', 'Cwd': '.'}}, 'stepIdx': 3}
    result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True)
    assert result.returncode == 0 and json.loads(result.stdout)['decision'] == 'deny'
    event['toolCall']['args']['CommandLine'] = 'git status'
    result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True)
    assert result.stdout == ''
