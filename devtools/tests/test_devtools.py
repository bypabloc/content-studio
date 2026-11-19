"""devtools del flujo de agentes: worktree, gpu-turn, agent-context y rules."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from devtools import agent_context, gpu_turn, paths, rules, worktree
from devtools.__main__ import main as devtools

GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t']


def test_dispatch_and_errors():
    assert devtools([]) == 0
    assert devtools(['nothing']) == 2
    assert devtools(['worktree']) == 2
    assert devtools(['gpu-turn', 'run', '--', 'x']) == 2  # missing --job


def test_missing_and_links_not_touch_the_destination(tmp_path):
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    (main / 'server/data/narration/.venv-qwen/bin').mkdir(parents=True)
    (main / 'server/data/narration/.venv-qwen/bin/python').write_text('x')
    (main / 'server/data/music/models/ace').mkdir(parents=True)
    (main / 'server/data/narration/reference').mkdir(parents=True)
    (main / 'server/data/narration/reference/clara.wav').write_bytes(b'RIFF')
    (main / 'server/data/narration/voices/yesid').mkdir(parents=True)
    (wt / 'server/data/narration/reference').mkdir(parents=True)
    folders, audios = worktree.missing(main, wt)
    names = sorted(p.as_posix() for p in folders)
    assert names == [
        'server/data/music/models',
        'server/data/narration/.venv-qwen',
        'server/data/narration/voices/yesid',
    ]
    assert [a.as_posix() for a in audios] == ['server/data/narration/reference/clara.wav']
    for rel in folders:
        worktree.link(main / rel, wt / rel)
    assert (wt / 'server/data/narration/.venv-qwen/bin/python').read_text() == 'x'
    assert worktree.missing(main, wt)[0] == []
    assert worktree.remove_links(wt) == 3
    assert (main / 'server/data/narration/.venv-qwen/bin/python').is_file()  # el principal queda intacto
    assert not (wt / 'server/data/narration/.venv-qwen').exists()


def test_prepare_and_close_in_a_repo_real(tmp_path, monkeypatch):
    main = tmp_path / 'repo'
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'dev', str(remote)], check=True)
    subprocess.run(['git', 'clone', '-q', str(remote), str(main)], check=True, capture_output=True)
    # Sin `/` final, como el .gitignore del repo: en POSIX el enlace es un symlink, no una carpeta para git.
    (main / '.gitignore').write_text('models\ntmp/\n')
    (main / 'server/data/music/models/ace').mkdir(parents=True)
    subprocess.run([*GIT, 'add', '.'], cwd=main, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=main, check=True)
    subprocess.run(['git', 'push', '-q', 'origin', 'HEAD:dev'], cwd=main, check=True, capture_output=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'feature/tema'], cwd=main, check=True)
    monkeypatch.chdir(main)
    assert worktree.prepare(main.resolve(), 'tema') == 0
    assert (wt / 'server/data/music/models/ace').is_dir() and (wt / 'tmp').is_dir()
    (main / 'tmp/handoff/tema').mkdir(parents=True)
    (main / 'tmp/handoff/.sessions').mkdir()
    (main / 'tmp/handoff/.sessions/s1').write_text('tema')
    subprocess.run(['git', 'fetch', '-q', 'origin'], cwd=main, check=True)
    assert worktree.close(main.resolve(), 'tema', 'tema') == 0
    assert not wt.exists() and (main / 'server/data/music/models/ace').is_dir()
    assert not (main / 'tmp/handoff/tema').exists() and not (main / 'tmp/handoff/.sessions/s1').exists()
    assert worktree.close(main.resolve(), 'tema', 'tema') == 2


def test_missing_links_node_modules_so_spelling_works_in_a_worktree(tmp_path):
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    (main / 'node_modules/@cspell').mkdir(parents=True)
    wt.mkdir()
    assert [p.as_posix() for p in worktree.missing(main, wt)[0]] == ['node_modules']


def test_close_finishes_when_windows_cannot_delete_the_held_folder(tmp_path, monkeypatch):
    """Regresión: en Windows, `git worktree remove` vacía y desregistra el worktree pero falla al borrar la carpeta
    que otro proceso tiene como cwd («Permission denied»); `close` cortaba ahí y dejaba las ramas y el handoff."""
    main = tmp_path / 'repo'
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'dev', str(remote)], check=True)
    subprocess.run(['git', 'clone', '-q', str(remote), str(main)], check=True, capture_output=True)
    (main / 'a.txt').write_text('a')
    subprocess.run([*GIT, 'add', '.'], cwd=main, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=main, check=True)
    subprocess.run(['git', 'push', '-q', 'origin', 'HEAD:dev'], cwd=main, check=True, capture_output=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'fix/tema'], cwd=main, check=True)
    subprocess.run(['git', 'fetch', '-q', 'origin'], cwd=main, check=True)
    real = worktree._git

    def git_held(cwd, *args):
        r = real(cwd, *args)
        if args[:2] == ('worktree', 'remove'):
            wt.mkdir(parents=True, exist_ok=True)  # la carpeta vacía que Windows no deja borrar
            return subprocess.CompletedProcess(r.args, 1, '', "error: failed to delete '...': Permission denied")
        return r

    monkeypatch.setattr(worktree, '_git', git_held)
    monkeypatch.chdir(main)
    assert worktree.close(main.resolve(), 'tema', 'tema') == 0
    assert 'fix/tema' not in real(main, 'branch', '--list', 'fix/tema').stdout
    assert worktree.search(main.resolve(), 'tema') is None


def test_gpu_turn_takes_releases_and_clears_orphans(tmp_path):
    assert gpu_turn.take(tmp_path, 't1', ['python', 'cli.py']) is None
    owner = gpu_turn.take(tmp_path, 't2', ['otro'])
    assert owner['work'] == 't1'  # ocupada por este mismo proceso
    gpu_turn.release(tmp_path)
    assert gpu_turn.read(tmp_path) is None
    orphan = {'pid': 2**22 + 12345, 'platform': sys.platform, 'work': 'viejo', 'command': 'x'}
    gpu_turn.lock(tmp_path).write_text(json.dumps(orphan))
    assert gpu_turn.read(tmp_path) is None  # su proceso murió
    assert gpu_turn.take(tmp_path, 't3', ['y']) is None
    gpu_turn.release(tmp_path)


def test_turn_gpu_of_other_sistema_counts_como_busy(tmp_path):
    lock = gpu_turn.lock(tmp_path)
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({'pid': 1, 'platform': 'otro-sistema', 'work': 'wsl'}))
    assert gpu_turn.read(tmp_path)['work'] == 'wsl'


def test_gpu_turn_run_releases_even_if_it_fails(tmp_path):
    assert gpu_turn.run(tmp_path, 't', [sys.executable, '-c', 'raise SystemExit(3)']) == 3
    assert not gpu_turn.lock(tmp_path).exists()


def test_context_agents_the_repo_without_failures():
    agents, failures = agent_context.measure(paths.ROOT)
    assert failures == []
    assert agents['antigravity']['files'] > 0


def test_agent_context_accepts_rules_with_crlf(tmp_path):
    """Regresión: en Windows, git hace checkout con CRLF y el frontmatter no se reconocía."""
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/x.md').write_bytes(b'---\r\ntrigger: always_on\r\n---\r\n\r\n# X\r\n')
    assert agent_context.measure(tmp_path)[1] == []


def test_context_agents_detects_trigger_invalid(tmp_path):
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/x.md').write_text('---\ntrigger: siempre\n---\n# X\n')
    assert any('trigger' in f for f in agent_context.measure(tmp_path)[1])


def test_rules_syncs_keeping_the_frontmatter_of_claude(tmp_path):
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.claude/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/r.md').write_text('---\ntrigger: always_on\n---\n\n# R nueva\n', newline='\n')
    (tmp_path / '.claude/rules/r.md').write_text('---\npaths:\n  - "src/**"\n---\n\n# R vieja\n', newline='\n')
    (tmp_path / '.claude/rules/huerfana.md').write_text('# H\n')
    assert len(rules.differences(tmp_path)) == 2
    assert rules.sync(tmp_path) == ['.claude/rules/r.md']
    text = (tmp_path / '.claude/rules/r.md').read_text()
    assert text.startswith('---\npaths:') and text.endswith('# R nueva\n')
    assert rules.differences(tmp_path) == ['.claude/rules/huerfana.md has no source in .agents/rules/']


@pytest.mark.skipif(os.name != 'nt', reason='junctions solo en Windows')
def test_is_link_recognizes_junctions(tmp_path):
    (tmp_path / 'destino').mkdir()
    worktree.link(tmp_path / 'destino', tmp_path / 'enlace')
    assert worktree.is_link(tmp_path / 'enlace') and not worktree.is_link(tmp_path / 'destino')


def test_ac3_help_list_commands():
    """AC-3: devtools vive en la raíz; `python -m devtools --help` lista sus comandos y sale con 0."""
    r = subprocess.run([sys.executable, '-m', 'devtools', '--help'], cwd=paths.ROOT, capture_output=True, text=True)
    assert r.returncode == 0
    assert all(c in r.stderr for c in ('worktree', 'gpu-turn', 'agent-context', 'rules', 'move-data'))
