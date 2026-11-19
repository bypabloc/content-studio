"""Hooks de .claude/hooks y .git-hooks: se ejecutan de verdad (git corre los suyos con su propio shell)."""

from __future__ import annotations

import doctest
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', f'core.hooksPath={RAIZ / ".git-hooks"}']


def hook(nombre: str, payload: dict, *args: str) -> subprocess.CompletedProcess:
    ruta = RAIZ / '.claude' / 'hooks' / nombre
    return subprocess.run([sys.executable, str(ruta), *args], input=json.dumps(payload), capture_output=True, text=True)


@pytest.mark.parametrize(
    ('ruta', 'agente', 'codigo'),
    [('out/spec.png', None, 2), ('out/spec.PNG', 'image-reader', 0), ('src/a.py', None, 0)],
)
def test_image_read_guard(ruta, agente, codigo):
    payload = {'tool_input': {'file_path': ruta}, **({'agent_type': agente} if agente else {})}
    assert hook('image_read_guard.py', payload).returncode == codigo


def test_format_on_save_solo_lo_que_lintea_ci():
    sys.path.insert(0, str(RAIZ / '.claude' / 'hooks'))
    from format_on_save import relativa

    assert relativa(str(RAIZ / 'src' / 'a.py')) == 'src/a.py'
    assert relativa('cli.py') == 'cli.py'
    assert relativa('narration/README.md') is None
    assert relativa(str(RAIZ.parent / 'otro' / 'a.py')) is None


def test_session_start_compact_reinyecta_reglas():
    assert 'Un modelo a la vez' in hook('session_start.py', {}, 'compact').stdout


@pytest.mark.parametrize(
    'modulo', ['graphify_guard', 'image_read_guard', 'safe_compound', 'verify_state', 'worktree_guard']
)
def test_doctests_de_los_hooks(modulo):
    sys.path.insert(0, str(RAIZ / '.claude' / 'hooks'))
    assert doctest.testmod(importlib.import_module(modulo)).failed == 0


@pytest.mark.parametrize(
    ('comando', 'codigo'),
    [
        ('git worktree add .worktrees/x -b feature/x origin/dev', 2),
        ('git status && git worktree add tmp/x', 2),
        ('git worktree add ../content-studio-worktrees/x -b feature/x origin/dev', 0),
        ('git worktree list', 0),
    ],
)
def test_worktree_guard_bloquea_dentro_del_repo(comando, codigo):
    assert hook('worktree_guard.py', {'tool_input': {'command': comando}, 'cwd': str(RAIZ)}).returncode == codigo


def test_safe_compound_aprueba_solo_lo_permitido():
    def decision(comando: str) -> str:
        salida = hook('safe_compound.py', {'tool_input': {'command': comando}}).stdout
        return json.loads(salida)['hookSpecificOutput']['permissionDecision'] if salida else ''

    assert decision('uv run pytest -q > tmp/u.log 2>&1 && git log --oneline -1') == 'allow'
    assert decision('git status && rm -rf out') == ''
    assert decision('uv run pytest > src/x.py') == ''
    assert decision('git status') == ''  # simple: lo resuelve el harness


def test_graphify_guard_sugiere_en_codigo_y_calla_en_datos():
    sys.path.insert(0, str(RAIZ / '.claude' / 'hooks'))
    from graphify_guard import should_suggest

    assert should_suggest('search', {'command': 'grep -rn usar_venv src/content_studio'}, str(RAIZ))
    assert not should_suggest('search', {'command': 'grep -n qwen narration/README.md'}, str(RAIZ))
    assert should_suggest('read', {'file_path': str(RAIZ / 'src/content_studio/rutas.py')}, str(RAIZ))
    assert not should_suggest('read', {'file_path': 'docs/specs/README.md'}, str(RAIZ))


@pytest.fixture
def repo(tmp_path):
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp_path)], check=True)
    (tmp_path / 'a.txt').write_text('a')
    subprocess.run(['git', 'add', 'a.txt'], cwd=tmp_path, check=True)
    return tmp_path


def commit(repo: Path, mensaje: str) -> subprocess.CompletedProcess:
    return subprocess.run([*GIT, 'commit', '-q', '-m', mensaje], cwd=repo, capture_output=True, text=True)


def test_pre_commit_rechaza_main_y_audio(repo):
    assert commit(repo, 'docs: a').returncode == 1
    subprocess.run(['git', 'switch', '-q', '-c', 'feature/voz'], cwd=repo, check=True)
    (repo / 'voz.wav').write_bytes(b'RIFF')
    subprocess.run(['git', 'add', '-f', 'voz.wav'], cwd=repo, check=True)
    assert 'voz.wav' in commit(repo, 'feat: voz').stderr


def test_prepare_commit_msg_quita_atribucion_y_pre_push_protege_main(repo, tmp_path_factory):
    subprocess.run(['git', 'switch', '-q', '-c', 'docs/a'], cwd=repo, check=True)
    assert commit(repo, 'docs: a\n\nCo-Authored-By: Claude <noreply@anthropic.com>').returncode == 0
    log = subprocess.run(['git', 'log', '-1', '--format=%B'], cwd=repo, capture_output=True, text=True).stdout
    assert log.strip() == 'docs: a'

    remoto = tmp_path_factory.mktemp('remoto')
    subprocess.run(['git', 'init', '-q', '--bare', str(remoto)], check=True)
    push = [*GIT, 'push', '-q', str(remoto)]
    assert subprocess.run([*push, 'docs/a:main'], cwd=repo, capture_output=True).returncode == 1
    assert subprocess.run([*push, 'docs/a:sinprefijo'], cwd=repo, capture_output=True).returncode == 1
    assert subprocess.run([*push, 'docs/a'], cwd=repo, capture_output=True).returncode == 0

    (repo / 'tests/tdd').mkdir(parents=True)
    (repo / 'tests/tdd/test_x.py').write_text('')
    subprocess.run(['git', 'add', 'tests'], cwd=repo, check=True)
    # Sin los hooks del repo: el pre-commit correría ruff y pytest de content-studio en este repo vacío.
    subprocess.run([*GIT[:5], 'commit', '-qm', 'test: tdd'], cwd=repo, check=True)
    tdd = subprocess.run([*push, 'docs/a'], cwd=repo, capture_output=True, text=True)
    assert tdd.returncode == 1 and 'tests/tdd/test_x.py' in tdd.stderr
