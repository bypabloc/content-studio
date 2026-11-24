"""`spelling`: cspell sobre identificadores, no sobre docstrings ni comentarios (spec 002, AC-1 y AC-2)."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from devtools import paths, spelling
from devtools.__main__ import main as devtools

GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t']
requires_bun = pytest.mark.skipif(shutil.which('bun') is None, reason='bun is not installed')


@requires_bun
def test_ac2_identifiers_if_docstrings_and_comments_not(tmp_path):
    source = tmp_path / 'duracion.py'
    source.write_text(
        'def calcular_duracion():\n    """Calcula la duración."""\n    # pausa larga\n    return 1\n',
        encoding='utf-8',
    )
    words = {d.split(' ')[-1] for d in spelling.review([source])}
    assert {'calcular', 'duracion'} <= words
    assert not words & {'Calcula', 'calcula', 'pausa', 'larga', 'duración'}


@requires_bun
def test_ac3_gate_the_pre_commit_rejects_identifier_in_spanish(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()
    subprocess.run([*GIT, 'init', '-q', '-b', 'feature/gate-spelling'], cwd=repo, check=True)
    (repo / 'calculo.py').write_text('def calcular_total():\n    return 1\n', encoding='utf-8')
    subprocess.run([*GIT, 'add', 'calculo.py'], cwd=repo, check=True)
    # El hook corre `python -m devtools` desde el repo temporal: el paquete y el config salen del checkout real.
    monkeypatch.setenv('PYTHONPATH', str(paths.ROOT))
    commit = subprocess.run(
        [*GIT, '-c', f'core.hooksPath={paths.ROOT / ".git-hooks"}', 'commit', '-q', '-m', 'feat: prueba'],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert commit.returncode != 0
    assert 'calculo.py:1 calcular' in commit.stderr


@requires_bun
def test_ac1_code_in_english_exits_0_and_json_with_issues_0(tmp_path, capsys):
    source = tmp_path / 'duration.py'
    source.write_text('def compute_duration():\n    """Compute the duration."""\n    return 1\n', encoding='utf-8')
    assert devtools(['spelling', str(source)]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1]) == {'issues': 0, 'detail': []}
