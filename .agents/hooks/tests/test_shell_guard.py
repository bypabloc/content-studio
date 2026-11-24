"""shell_guard.py ejecutado de verdad, como lo llaman Claude Code y Codex: JSON por stdin, exit 2 bloquea."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / 'shell_guard.py'


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


@pytest.mark.parametrize(
    ('tool_input', 'code'),
    [
        # el caso del lote 001-017: reproducir la CI de Linux en WSL, también en segundo plano
        ({'command': "wsl -e bash -lc 'cd /mnt/d/x && uv run pytest -q'", 'run_in_background': True}, 2),
        ({'command': 'MSYS_NO_PATHCONV=1 wsl -d Ubuntu-24.04 -- bash /mnt/d/x/repro.sh'}, 2),
        ({'command': 'gh run view 123 --log-failed'}, 0),
    ],
)
def test_blocks_wsl_even_in_the_background(tool_input, code):
    result = run(tool_input)
    assert result.returncode == code
    assert ('WSL' in result.stderr) == (code == 2)


@pytest.mark.parametrize(
    ('command', 'code'),
    [
        ('git add -A && git commit --no-verify -m "fix: x"', 2),
        ('git push --no-verify -u origin feature/x', 2),
        ('git commit -n -m "fix: x"', 2),
        ('git -c core.hooksPath=/dev/null push origin feature/x', 2),
        ('git commit -m "docs: nunca --no-verify"', 0),
        ('git push -u origin feature/x', 0),
    ],
)
def test_blocks_skipping_the_git_hooks(command, code):
    result = run({'command': command})
    assert result.returncode == code
    assert ('--no-verify' in result.stderr) == (code == 2)


def test_bad_input_does_not_block():
    assert subprocess.run([sys.executable, str(HOOK)], input='no json', capture_output=True, text=True).returncode == 0


def test_antigravity_gets_a_json_deny_on_stdout():
    event = {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'sleep 60', 'Cwd': '.'}}, 'stepIdx': 3}
    result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True)
    assert result.returncode == 0 and json.loads(result.stdout)['decision'] == 'deny'
    event['toolCall']['args']['CommandLine'] = 'git status'
    result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True)
    assert result.stdout == ''


@pytest.mark.parametrize('command', ['sleep 60', 'wsl -l -v', 'git commit --no-verify -m x'])
def test_the_message_says_what_why_and_instead(command):
    stderr = run({'command': command}).stderr
    assert all(part in stderr for part in ('Blocked by', 'Why:', 'Instead:'))


def test_a_variable_named_like_the_command_is_not_blocked():
    """Regresión: `wsl=0` en un script de Python bloqueaba la revisión del lote."""
    assert run({'command': "python - <<'EOF'\nout=[]; wsl=0; rem=0\nEOF"}).returncode == 0
