"""devtools del flujo de agentes: worktree, turno-gpu, contexto-agentes y reglas."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from devtools import contexto_agentes, reglas, rutas, turno_gpu, worktree
from devtools.__main__ import main as devtools

GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t']


def test_despacho_y_errores():
    assert devtools([]) == 0
    assert devtools(['nada']) == 2
    assert devtools(['worktree']) == 2
    assert devtools(['turno-gpu', 'run', '--', 'x']) == 2  # falta --trabajo


def test_faltantes_y_enlaces_no_tocan_el_destino(tmp_path):
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    (main / 'server/data/narration/.venv-qwen/bin').mkdir(parents=True)
    (main / 'server/data/narration/.venv-qwen/bin/python').write_text('x')
    (main / 'server/data/music/models/ace').mkdir(parents=True)
    (main / 'server/data/narration/voz').mkdir(parents=True)
    (main / 'server/data/narration/voz/clara.wav').write_bytes(b'RIFF')
    (main / 'server/data/narration/voces/yesid').mkdir(parents=True)
    (wt / 'server/data/narration/voz').mkdir(parents=True)
    carpetas, audios = worktree.faltantes(main, wt)
    nombres = sorted(p.as_posix() for p in carpetas)
    assert nombres == [
        'server/data/music/models',
        'server/data/narration/.venv-qwen',
        'server/data/narration/voces/yesid',
    ]
    assert [a.as_posix() for a in audios] == ['server/data/narration/voz/clara.wav']
    for rel in carpetas:
        worktree.enlazar(main / rel, wt / rel)
    assert (wt / 'server/data/narration/.venv-qwen/bin/python').read_text() == 'x'
    assert worktree.faltantes(main, wt)[0] == []
    assert worktree.quitar_enlaces(wt) == 3
    assert (main / 'server/data/narration/.venv-qwen/bin/python').is_file()  # el principal queda intacto
    assert not (wt / 'server/data/narration/.venv-qwen').exists()


def test_prepare_y_close_en_un_repo_real(tmp_path, monkeypatch):
    main = tmp_path / 'repo'
    remoto = tmp_path / 'remoto.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'dev', str(remoto)], check=True)
    subprocess.run(['git', 'clone', '-q', str(remoto), str(main)], check=True, capture_output=True)
    # Sin `/` final, como el .gitignore del repo: en POSIX el enlace es un symlink, no una carpeta para git.
    (main / '.gitignore').write_text('models\ntmp/\n')
    (main / 'server/data/music/models/ace').mkdir(parents=True)
    subprocess.run([*GIT, 'add', '.'], cwd=main, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=main, check=True)
    subprocess.run(['git', 'push', '-q', 'origin', 'HEAD:dev'], cwd=main, check=True, capture_output=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'feature/tema'], cwd=main, check=True)
    monkeypatch.chdir(main)
    assert worktree.preparar(main.resolve(), 'tema') == 0
    assert (wt / 'server/data/music/models/ace').is_dir() and (wt / 'tmp').is_dir()
    (main / 'tmp/handoff/tema').mkdir(parents=True)
    (main / 'tmp/handoff/.sessions').mkdir()
    (main / 'tmp/handoff/.sessions/s1').write_text('tema')
    subprocess.run(['git', 'fetch', '-q', 'origin'], cwd=main, check=True)
    assert worktree.cerrar(main.resolve(), 'tema', 'tema') == 0
    assert not wt.exists() and (main / 'server/data/music/models/ace').is_dir()
    assert not (main / 'tmp/handoff/tema').exists() and not (main / 'tmp/handoff/.sessions/s1').exists()
    assert worktree.cerrar(main.resolve(), 'tema', 'tema') == 2


def test_turno_gpu_toma_suelta_y_libera_huerfanos(tmp_path):
    assert turno_gpu.tomar(tmp_path, 't1', ['python', 'cli.py']) is None
    dueño = turno_gpu.tomar(tmp_path, 't2', ['otro'])
    assert dueño['work'] == 't1'  # ocupada por este mismo proceso
    turno_gpu.soltar(tmp_path)
    assert turno_gpu.leer(tmp_path) is None
    huerfano = {'pid': 2**22 + 12345, 'platform': sys.platform, 'work': 'viejo', 'command': 'x'}
    turno_gpu.candado(tmp_path).write_text(json.dumps(huerfano))
    assert turno_gpu.leer(tmp_path) is None  # su proceso murió
    assert turno_gpu.tomar(tmp_path, 't3', ['y']) is None
    turno_gpu.soltar(tmp_path)


def test_turno_gpu_de_otro_sistema_cuenta_como_ocupada(tmp_path):
    candado = turno_gpu.candado(tmp_path)
    candado.parent.mkdir(parents=True)
    candado.write_text(json.dumps({'pid': 1, 'platform': 'otro-sistema', 'work': 'wsl'}))
    assert turno_gpu.leer(tmp_path)['work'] == 'wsl'


def test_turno_gpu_run_suelta_aunque_falle(tmp_path):
    assert turno_gpu.run(tmp_path, 't', [sys.executable, '-c', 'raise SystemExit(3)']) == 3
    assert not turno_gpu.candado(tmp_path).exists()


def test_contexto_agentes_del_repo_sin_fallos():
    agentes, fallos = contexto_agentes.medir(rutas.RAIZ)
    assert fallos == []
    assert agentes['antigravity']['files'] > 0


def test_contexto_agentes_acepta_reglas_con_crlf(tmp_path):
    """Regresión: en Windows, git hace checkout con CRLF y el frontmatter no se reconocía."""
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/x.md').write_bytes(b'---\r\ntrigger: always_on\r\n---\r\n\r\n# X\r\n')
    assert contexto_agentes.medir(tmp_path)[1] == []


def test_contexto_agentes_detecta_trigger_invalido(tmp_path):
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/x.md').write_text('---\ntrigger: siempre\n---\n# X\n')
    assert any('trigger' in f for f in contexto_agentes.medir(tmp_path)[1])


def test_reglas_sincroniza_conservando_el_frontmatter_de_claude(tmp_path):
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.claude/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/r.md').write_text('---\ntrigger: always_on\n---\n\n# R nueva\n', newline='\n')
    (tmp_path / '.claude/rules/r.md').write_text('---\npaths:\n  - "src/**"\n---\n\n# R vieja\n', newline='\n')
    (tmp_path / '.claude/rules/huerfana.md').write_text('# H\n')
    assert len(reglas.diferencias(tmp_path)) == 2
    assert reglas.sincronizar(tmp_path) == ['.claude/rules/r.md']
    texto = (tmp_path / '.claude/rules/r.md').read_text()
    assert texto.startswith('---\npaths:') and texto.endswith('# R nueva\n')
    assert reglas.diferencias(tmp_path) == ['.claude/rules/huerfana.md sin fuente en .agents/rules/']


@pytest.mark.skipif(os.name != 'nt', reason='junctions solo en Windows')
def test_es_enlace_reconoce_junctions(tmp_path):
    (tmp_path / 'destino').mkdir()
    worktree.enlazar(tmp_path / 'destino', tmp_path / 'enlace')
    assert worktree.es_enlace(tmp_path / 'enlace') and not worktree.es_enlace(tmp_path / 'destino')


def test_ac3_help_lista_comandos():
    """AC-3: devtools vive en la raíz; `python -m devtools --help` lista sus comandos y sale con 0."""
    r = subprocess.run([sys.executable, '-m', 'devtools', '--help'], cwd=rutas.RAIZ, capture_output=True, text=True)
    assert r.returncode == 0
    assert all(c in r.stderr for c in ('worktree', 'turno-gpu', 'agent-context', 'rules', 'move-data'))
