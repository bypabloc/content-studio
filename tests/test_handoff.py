"""Hook de handoff (.agents/hooks/session_handoff.py): vínculo por sesión, mensajes, Stop, AskUserQuestion y estado."""

from __future__ import annotations

import doctest
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
HOOKS = RAIZ / '.agents' / 'hooks'
sys.path.insert(0, str(HOOKS))

import handoff_text as T  # noqa: E402
import session_handoff as H  # noqa: E402

PENDIENTE = 'Status: in-progress\nPhase: implementation\nNext step: commit del grupo 2\n'


def trabajo(raiz: Path, nombre: str, progress: str = PENDIENTE, sesion: str | None = 's1') -> Path:
    carpeta = raiz / 'tmp/handoff' / nombre
    carpeta.mkdir(parents=True)
    (carpeta / 'PROGRESS.md').write_text(progress, encoding='utf-8')
    if sesion:
        (raiz / 'tmp/handoff/.sessions').mkdir(exist_ok=True)
        (raiz / 'tmp/handoff/.sessions' / sesion).write_text(nombre, encoding='utf-8')
    return carpeta


def test_doctests_de_los_textos():
    assert doctest.testmod(T).failed == 0


def test_vinculo_por_sesion_y_por_numero_de_rama(tmp_path):
    trabajo(tmp_path, '012-musica-cinematic')
    assert H.current_work(tmp_path, 's1', 'dev') == '012-musica-cinematic'
    assert H.current_work(tmp_path, 'otra', 'feature/012-musica-cinematic') == '012-musica-cinematic'
    assert H.current_work(tmp_path, 'otra', 'dev') is None
    assert H.current_work(tmp_path, '../s1', 'dev') is None  # id inseguro


def test_mensaje_con_trabajo_incluye_archivos_y_turno_gpu(tmp_path):
    trabajo(tmp_path, 'tema')
    msg = H.build_message(tmp_path, 'feature/tema', 'compact', 's1')
    assert msg.startswith(T.HEADER.split('{')[0])
    assert 'turno-gpu run' in msg and '--- PROGRESS.md ---' in msg and 'DECISIONS.md: falta' in msg


def test_mensaje_sin_trabajo_pide_vinculo_y_lista_activos(tmp_path):
    trabajo(tmp_path, 'ajeno', sesion=None)
    msg = H.build_message(tmp_path, 'dev', 'startup', 'nueva')
    assert 'nueva' in msg and '- ajeno: commit del grupo 2' in msg
    assert H.build_message(tmp_path, 'dev', 'startup', '') == ''


def test_stop_bloquea_hasta_el_tope_y_libera_con_done(tmp_path):
    carpeta = trabajo(tmp_path, 'tema')
    for _ in range(H.MAX_BLOCKS):
        assert json.loads(H.stop_reply(tmp_path, 's1', 'dev'))['decision'] == 'block'
    assert H.stop_reply(tmp_path, 's1', 'dev') == ''  # tope anti-bucle
    (carpeta / 'PROGRESS.md').write_text('Status: done\nNext step: nada\n', encoding='utf-8')
    assert H.stop_reply(tmp_path, 's1', 'dev') == ''


@pytest.mark.parametrize(
    ('status', 'bloquea'),
    [('blocked — taste: elegir la toma', False), ('blocked — no sé qué motor usar', True), ('in-progress', True)],
)
def test_stop_solo_libera_bloqueos_del_usuario(tmp_path, status, bloquea):
    trabajo(tmp_path, 'tema', f'Status: {status}\nNext step: seguir\n')
    assert bool(H.stop_reply(tmp_path, 's1', 'dev')) is bloquea


def test_external_wait_deja_parar(tmp_path):
    trabajo(tmp_path, 'tema', 'Status: in-progress\nPhase: external-wait\nNext step: esperar CI\n')
    assert H.stop_reply(tmp_path, 's1', 'dev') == ''


def test_ask_se_rechaza_solo_con_spec_en_ejecucion(tmp_path):
    trabajo(tmp_path, '012-musica')
    assert H.ask_reply(tmp_path, tmp_path, 's1', 'dev') == ''  # sin carpeta de spec: diseño o entrevista
    (tmp_path / 'docs/specs/012-musica').mkdir(parents=True)
    salida = json.loads(H.ask_reply(tmp_path, tmp_path, 's1', 'dev'))
    assert salida['hookSpecificOutput']['permissionDecision'] == 'deny'


def test_progress_largo_se_avisa_al_escribirlo(tmp_path):
    carpeta = trabajo(tmp_path, 'tema', 'Status: in-progress\nCurrent: ' + 'x' * 130 + '\nNext step: y\n')
    payload = {'tool_input': {'file_path': str(carpeta / 'PROGRESS.md')}}
    assert 'Current' in json.loads(H.progress_reply(payload))['reason']
    assert H.progress_reply({'tool_input': {'file_path': str(tmp_path / 'otro.md')}}) == ''


def test_render_por_agente():
    assert json.loads(H.render('m'))['hookSpecificOutput']['additionalContext'] == 'm'
    assert json.loads(H.render('m', 'antigravity'))['injectSteps'][0]['ephemeralMessage'] == 'm'
    assert H.read_event({'conversationId': 'c', 'workspacePaths': ['/r']}) == ('c', '/r', 'invocation', 'antigravity')


def test_script_real_status_y_bitacora(tmp_path):
    """El script como lo llaman el mod y los hooks: en un repo git, con su stdin."""
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    trabajo(tmp_path, 'tema')
    payload = json.dumps({'session_id': 's1', 'cwd': str(tmp_path)})
    run = [sys.executable, str(HOOKS / 'session_handoff.py')]
    estado = subprocess.run([*run, '--status'], input=payload, capture_output=True, text=True, check=True)
    assert json.loads(estado.stdout) == {'work': 'tema', 'status': 'in-progress', 'phase': 'implementation',
                                         'next_step': 'commit del grupo 2'}  # fmt: skip
    inicio = json.dumps({'session_id': 's1', 'cwd': str(tmp_path), 'source': 'startup'})
    salida = subprocess.run(run, input=inicio, capture_output=True, text=True, check=True).stdout
    assert 'Sesión nueva' in json.loads(salida)['hookSpecificOutput']['additionalContext']
    assert (tmp_path / 'tmp/handoff/.log/events.jsonl').is_file()
