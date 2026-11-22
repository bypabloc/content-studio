"""computer_use_guard.py ejecutado de verdad, con el evento de cada agente (spec 024, AC-1 y AC-2)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / 'computer_use_guard.py'


def run(event: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True)


@pytest.mark.parametrize(
    ('tool_name', 'tool_input'),
    [
        ('mcp__computer-use__screenshot', {}),
        ('mcp__remote-devices__computer_click', {'x': 1}),
        ('mcp__node_repl__js', {'code': 'const { sky } = await import("@oai/sky");'}),
        # el caso del lote 012: Codex en modo código llama a node_repl desde exec
        ('exec', {'code': 'await tools.mcp__node_repl__js({code: "globalThis.apps = await sky.list_apps()"})'}),
        ('js', {'code': 'await sky.launch_app({ app: "content-studio.exe" })'}),
    ],
)
def test_ac1_blocks_computer_use_tools_and_sky_code(tool_name, tool_input):
    result = run({'tool_name': tool_name, 'tool_input': tool_input})
    assert result.returncode == 2
    assert 'Blocked by .agents/hooks/computer_use_guard.py' in result.stderr
    assert 'python -m devtools app-check run' in result.stderr


@pytest.mark.parametrize(
    ('tool_name', 'tool_input'),
    [
        ('Bash', {'command': 'git commit -m "docs: sin sky ni computer use"'}),
        ('mcp__node_repl__js', {'code': 'console.log(1)'}),
        ('exec', {'code': 'text("el cielo (sky) está despejado")'}),
        ('Read', {'file_path': 'docs/sky.md'}),
        ('mcp__engram__mem_search', {'query': 'computer use'}),
    ],
)
def test_ac2_lets_other_tools_and_mentions_pass(tool_name, tool_input):
    result = run({'tool_name': tool_name, 'tool_input': tool_input})
    assert (result.returncode, result.stdout, result.stderr) == (0, '', '')


def test_ac1_exit_code_per_agent():
    claude = run({'tool_name': 'mcp__computer-use__left_click', 'tool_input': {}, 'hook_event_name': 'PreToolUse'})
    codex = run({'tool_name': 'mcp__node_repl__js', 'tool_input': {'code': 'sky.list_apps()'}, 'turn_id': 't1'})
    assert claude.returncode == codex.returncode == 2
    antigravity = run({'toolCall': {'name': 'computer_click', 'args': {}}, 'stepIdx': 1})
    assert antigravity.returncode == 0
    assert json.loads(antigravity.stdout)['decision'] == 'deny'
    allowed = run({'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git status'}}, 'stepIdx': 2})
    assert (allowed.returncode, allowed.stdout) == (0, '')


def test_bad_input_does_not_block():
    result = subprocess.run([sys.executable, str(HOOK)], input='no json', capture_output=True, text=True)
    assert result.returncode == 0
