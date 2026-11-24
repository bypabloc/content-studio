"""Hooks de .claude/hooks y .git-hooks: se ejecutan de verdad (git corre los suyos con su propio shell)."""

from __future__ import annotations

import doctest
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .claude/hooks/tests/ → raíz del repo
GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', f'core.hooksPath={ROOT / ".git-hooks"}']


def hook(name: str, payload: dict, *args: str) -> subprocess.CompletedProcess:
    path = ROOT / '.claude' / 'hooks' / name
    return subprocess.run([sys.executable, str(path), *args], input=json.dumps(payload), capture_output=True, text=True)


@pytest.mark.parametrize(
    ('path', 'agent', 'code'),
    [('out/spec.png', None, 2), ('out/spec.PNG', 'image-reader', 0), ('src/a.py', None, 0)],
)
def test_image_read_guard(path, agent, code):
    payload = {'tool_input': {'file_path': path}, **({'agent_type': agent} if agent else {})}
    assert hook('image_read_guard.py', payload).returncode == code


def test_format_on_save_only_it_that_lints_ci():
    sys.path.insert(0, str(ROOT / '.claude' / 'hooks'))
    from format_on_save import relative

    assert relative(str(ROOT / 'server' / 'src' / 'a.py')) == 'server/src/a.py'
    assert relative('cli.py') == 'cli.py'
    assert relative('devtools/worktree.py') == 'devtools/worktree.py'
    assert relative('server/data/narration/README.md') is None
    assert relative(str(ROOT.parent / 'otro' / 'a.py')) is None


def test_session_start_compact_injects_rules_again():
    assert 'Un modelo a la vez' in hook('session_start.py', {}, 'compact').stdout


@pytest.mark.parametrize(
    'module',
    ['graphify_guard', 'image_read_guard', 'main_write_guard', 'safe_compound', 'verify_state', 'worktree_guard'],
)
def test_doctests_of_the_hooks(module):
    sys.path.insert(0, str(ROOT / '.claude' / 'hooks'))
    assert doctest.testmod(importlib.import_module(module)).failed == 0


@pytest.mark.parametrize(
    ('command', 'code'),
    [
        ('git worktree add .worktrees/x -b feature/x origin/dev', 2),
        ('git status && git worktree add tmp/x', 2),
        ('git worktree add ../content-studio-worktrees/x -b feature/x origin/dev', 0),
        ('git worktree list', 0),
    ],
)
def test_worktree_guard_blocks_inside_the_repo(command, code):
    assert hook('worktree_guard.py', {'tool_input': {'command': command}, 'cwd': str(ROOT)}).returncode == code


def test_safe_compound_approves_only_what_it_allows():
    def decision(command: str) -> str:
        output = hook('safe_compound.py', {'tool_input': {'command': command}}).stdout
        return json.loads(output)['hookSpecificOutput']['permissionDecision'] if output else ''

    assert decision('uv run pytest -q > tmp/u.log 2>&1 && git log --oneline -1') == 'allow'
    assert decision('git status && rm -rf out') == ''
    assert decision('uv run pytest > src/x.py') == ''
    assert decision('git status') == ''  # simple: lo resuelve el harness


def test_graphify_guard_suggests_in_code_and_stays_silent_in_data():
    sys.path.insert(0, str(ROOT / '.claude' / 'hooks'))
    from graphify_guard import should_suggest

    assert should_suggest('search', {'command': 'grep -rn usar_venv server/src/content_studio'}, str(ROOT))
    assert not should_suggest('search', {'command': 'grep -n qwen server/data/narration/README.md'}, str(ROOT))
    assert should_suggest('read', {'file_path': str(ROOT / 'server/src/content_studio/rutas.py')}, str(ROOT))
    assert not should_suggest('read', {'file_path': 'docs/specs/README.md'}, str(ROOT))


@pytest.fixture
def repo(tmp_path):
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp_path)], check=True)
    (tmp_path / 'a.txt').write_text('a')
    subprocess.run(['git', 'add', 'a.txt'], cwd=tmp_path, check=True)
    return tmp_path


def commit(repo: Path, message: str) -> subprocess.CompletedProcess:
    return subprocess.run([*GIT, 'commit', '-q', '-m', message], cwd=repo, capture_output=True, text=True)


def test_pre_commit_rejects_main_and_audio(repo):
    assert commit(repo, 'docs: a').returncode == 1
    subprocess.run(['git', 'switch', '-q', '-c', 'feature/voz'], cwd=repo, check=True)
    (repo / 'voz.wav').write_bytes(b'RIFF')
    subprocess.run(['git', 'add', '-f', 'voz.wav'], cwd=repo, check=True)
    assert 'voz.wav' in commit(repo, 'feat: voz').stderr


def test_prepare_commit_msg_removes_attribution_and_pre_push_protects_main(repo, tmp_path_factory):
    subprocess.run(['git', 'switch', '-q', '-c', 'docs/a'], cwd=repo, check=True)
    assert commit(repo, 'docs: a\n\nCo-Authored-By: Claude <noreply@anthropic.com>').returncode == 0
    log = subprocess.run(['git', 'log', '-1', '--format=%B'], cwd=repo, capture_output=True, text=True).stdout
    assert log.strip() == 'docs: a'

    remote = tmp_path_factory.mktemp('remote')
    subprocess.run(['git', 'init', '-q', '--bare', str(remote)], check=True)
    push = [*GIT, 'push', '-q', str(remote)]
    # Como el push de un test dentro del pre-push real: sin unit, que correría el pytest de content-studio aquí.
    inner = {**os.environ, 'CS_PRE_PUSH_INNER': '1'}
    assert subprocess.run([*push, 'docs/a:main'], cwd=repo, capture_output=True, env=inner).returncode == 1
    assert subprocess.run([*push, 'docs/a:sinprefijo'], cwd=repo, capture_output=True, env=inner).returncode == 1
    assert subprocess.run([*push, 'docs/a'], cwd=repo, capture_output=True, env=inner).returncode == 0

    (repo / 'server/tests/tdd').mkdir(parents=True)
    (repo / 'server/tests/tdd/test_x.py').write_text('')
    subprocess.run(['git', 'add', 'server'], cwd=repo, check=True)
    # Sin los hooks del repo: el pre-commit correría ruff y pytest de content-studio en este repo vacío.
    subprocess.run([*GIT[:5], 'commit', '-qm', 'test: tdd'], cwd=repo, check=True)
    tdd = subprocess.run([*push, 'docs/a'], cwd=repo, capture_output=True, text=True, env=inner)
    assert tdd.returncode == 1 and 'server/tests/tdd/test_x.py' in tdd.stderr


def test_every_block_says_what_why_and_instead():
    image = hook('image_read_guard.py', {'tool_input': {'file_path': 'out/spec.png'}}).stderr
    command = 'git worktree add .worktrees/x -b feature/x origin/dev'
    worktree = hook('worktree_guard.py', {'tool_input': {'command': command}, 'cwd': str(ROOT)}).stderr
    for stderr in (image, worktree):
        assert all(part in stderr for part in ('Blocked by', 'Why:', 'Instead:')), stderr


def test_main_write_guard_blocks_tracked_files_of_the_main_checkout_on_dev(tmp_path):
    main = tmp_path / 'repo'
    main.mkdir()
    subprocess.run(['git', 'init', '-q', '-b', 'dev', str(main)], check=True)
    (main / '.gitignore').write_text('tmp/\n')
    (main / 'a.md').write_text('a')
    bare = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'core.hooksPath=']  # sin los hooks del repo
    subprocess.run([*bare, 'add', '.'], cwd=main, check=True)
    subprocess.run([*bare, 'commit', '-qm', 'base'], cwd=main, check=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'feature/tema'], cwd=main, check=True)

    def edit(path, cwd=main):
        return hook('main_write_guard.py', {'tool_input': {'file_path': str(path)}, 'cwd': str(cwd)})

    blocked = edit(main / 'a.md', cwd=wt)
    assert blocked.returncode == 2
    assert all(part in blocked.stderr for part in ('Blocked by', 'Why:', 'Instead:', 'tema/a.md'))
    assert edit(main / 'nuevo.md').returncode == 2  # un archivo nuevo, también
    assert edit(main / 'tmp' / 'handoff' / 'PROGRESS.md').returncode == 0  # ignorado por git
    assert edit(wt / 'a.md', cwd=wt).returncode == 0
    subprocess.run(['git', 'switch', '-q', '-c', 'fix/chico'], cwd=main, check=True)
    assert edit(main / 'a.md').returncode == 0  # el principal en una rama de trabajo
