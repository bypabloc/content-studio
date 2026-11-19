"""`spelling`: cspell sobre identificadores, no sobre docstrings ni comentarios (spec 002, AC-1 y AC-2)."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from devtools import rutas, spelling
from devtools.__main__ import main as devtools

GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t']
requiere_bun = pytest.mark.skipif(shutil.which('bun') is None, reason='bun no está instalado')


@requiere_bun
def test_ac2_identificadores_si_docstrings_y_comentarios_no(tmp_path):
    fuente = tmp_path / 'duracion.py'
    fuente.write_text(
        'def calcular_duracion():\n    """Calcula la duración."""\n    # pausa larga\n    return 1\n',
        encoding='utf-8',
    )
    palabras = {d.split(' ')[-1] for d in spelling.revisar([fuente])}
    assert {'calcular', 'duracion'} <= palabras
    assert not palabras & {'Calcula', 'calcula', 'pausa', 'larga', 'duración'}


@requiere_bun
def test_ac3_gate_del_pre_commit_rechaza_identificador_en_espanol(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()
    subprocess.run([*GIT, 'init', '-q', '-b', 'feature/gate-spelling'], cwd=repo, check=True)
    (repo / 'calculo.py').write_text('def calcular_total():\n    return 1\n', encoding='utf-8')
    subprocess.run([*GIT, 'add', 'calculo.py'], cwd=repo, check=True)
    # El hook corre `python -m devtools` desde el repo temporal: el paquete y el config salen del checkout real.
    monkeypatch.setenv('PYTHONPATH', str(rutas.RAIZ))
    commit = subprocess.run(
        [*GIT, '-c', f'core.hooksPath={rutas.RAIZ / ".git-hooks"}', 'commit', '-q', '-m', 'feat: prueba'],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert commit.returncode != 0
    assert 'calculo.py:1 calcular' in commit.stderr


@requiere_bun
def test_ac1_codigo_en_ingles_sale_0_y_json_con_issues_0(tmp_path, capsys):
    fuente = tmp_path / 'duration.py'
    fuente.write_text('def compute_duration():\n    """Compute the duration."""\n    return 1\n', encoding='utf-8')
    assert devtools(['spelling', str(fuente)]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1]) == {'issues': 0, 'detalle': []}
