"""Hook de handoff (.agents/hooks/session_handoff.py): vínculo por sesión, mensajes, Stop, AskUserQuestion y estado."""

from __future__ import annotations

import doctest
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .agents/hooks/tests/ → raíz del repo
HOOKS = ROOT / '.agents' / 'hooks'
sys.path.insert(0, str(HOOKS))

import handoff_text as T  # noqa: E402
import session_handoff as H  # noqa: E402

PENDING = 'Status: in-progress\nPhase: implementation\nNext step: commit del grupo 2\n'


def job(root: Path, name: str, progress: str = PENDING, session: str | None = 's1') -> Path:
    folder = root / 'tmp/handoff' / name
    folder.mkdir(parents=True)
    (folder / 'PROGRESS.md').write_text(progress, encoding='utf-8')
    if session:
        (root / 'tmp/handoff/.sessions').mkdir(exist_ok=True)
        (root / 'tmp/handoff/.sessions' / session).write_text(name, encoding='utf-8')
    return folder


def test_doctests_of_the_texts():
    assert doctest.testmod(T).failed == 0


def test_link_per_session_and_per_branch_number(tmp_path):
    job(tmp_path, '012-musica-cinematic')
    assert H.current_work(tmp_path, 's1', 'dev') == '012-musica-cinematic'
    assert H.current_work(tmp_path, 'otra', 'feature/012-musica-cinematic') == '012-musica-cinematic'
    assert H.current_work(tmp_path, 'otra', 'dev') is None
    assert H.current_work(tmp_path, '../s1', 'dev') is None  # id inseguro


def test_message_with_job_includes_files_and_turn_gpu(tmp_path):
    job(tmp_path, 'tema')
    msg = H.build_message(tmp_path, 'feature/tema', 'compact', 's1')
    assert msg.startswith(T.HEADER.split('{')[0])
    assert 'gpu-turn run' in msg and '--- PROGRESS.md ---' in msg and 'DECISIONS.md: falta' in msg


def test_message_without_job_asks_link_and_list_active(tmp_path):
    job(tmp_path, 'ajeno', session=None)
    msg = H.build_message(tmp_path, 'dev', 'startup', 'nueva')
    assert 'nueva' in msg and '- ajeno: commit del grupo 2' in msg
    assert H.build_message(tmp_path, 'dev', 'startup', '') == ''


def test_stop_blocks_until_the_cap_and_releases_when_done(tmp_path):
    folder = job(tmp_path, 'tema')
    for _ in range(H.MAX_BLOCKS):
        assert json.loads(H.stop_reply(tmp_path, 's1', 'dev'))['decision'] == 'block'
    assert H.stop_reply(tmp_path, 's1', 'dev') == ''  # tope anti-bucle
    (folder / 'PROGRESS.md').write_text('Status: done\nNext step: nada\n', encoding='utf-8')
    assert H.stop_reply(tmp_path, 's1', 'dev') == ''


@pytest.mark.parametrize(
    ('status', 'blocks'),
    [('blocked — taste: elegir la toma', False), ('blocked — no sé qué motor usar', True), ('in-progress', True)],
)
def test_stop_only_releases_for_user_blocks(tmp_path, status, blocks):
    job(tmp_path, 'tema', f'Status: {status}\nNext step: seguir\n')
    assert bool(H.stop_reply(tmp_path, 's1', 'dev')) is blocks


def test_external_wait_leaves_stop(tmp_path):
    job(tmp_path, 'tema', 'Status: in-progress\nPhase: external-wait\nNext step: esperar CI\n')
    assert H.stop_reply(tmp_path, 's1', 'dev') == ''


def test_ask_rejects_only_with_spec_in_execution(tmp_path):
    job(tmp_path, '012-musica')
    assert H.ask_reply(tmp_path, tmp_path, 's1', 'dev') == ''  # sin carpeta de spec: diseño o entrevista
    (tmp_path / 'docs/specs/012-musica').mkdir(parents=True)
    output = json.loads(H.ask_reply(tmp_path, tmp_path, 's1', 'dev'))
    assert output['hookSpecificOutput']['permissionDecision'] == 'deny'


def test_progress_long_warns_al_writing_it(tmp_path):
    folder = job(tmp_path, 'tema', 'Status: in-progress\nCurrent: ' + 'x' * 130 + '\nNext step: y\n')
    payload = {'tool_input': {'file_path': str(folder / 'PROGRESS.md')}}
    assert 'Current' in json.loads(H.progress_reply(payload))['reason']
    assert H.progress_reply({'tool_input': {'file_path': str(tmp_path / 'otro.md')}}) == ''


def test_render_per_agent():
    assert json.loads(H.render('m'))['hookSpecificOutput']['additionalContext'] == 'm'
    assert json.loads(H.render('m', 'antigravity'))['injectSteps'][0]['ephemeralMessage'] == 'm'
    assert H.read_event({'conversationId': 'c', 'workspacePaths': ['/r']}) == ('c', '/r', 'invocation', 'antigravity')


def test_script_real_status_and_log(tmp_path):
    """El script como lo llaman el mod y los hooks: en un repo git, con su stdin."""
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    job(tmp_path, 'tema')
    payload = json.dumps({'session_id': 's1', 'cwd': str(tmp_path)})
    run = [sys.executable, str(HOOKS / 'session_handoff.py')]
    state = subprocess.run([*run, '--status'], input=payload, capture_output=True, text=True, check=True)
    assert json.loads(state.stdout) == {'work': 'tema', 'status': 'in-progress', 'phase': 'implementation',
                                         'next_step': 'commit del grupo 2'}  # fmt: skip
    start = json.dumps({'session_id': 's1', 'cwd': str(tmp_path), 'source': 'startup'})
    output = subprocess.run(run, input=start, capture_output=True, text=True, check=True).stdout
    assert 'Sesión nueva' in json.loads(output)['hookSpecificOutput']['additionalContext']
    assert (tmp_path / 'tmp/handoff/.log/events.jsonl').is_file()
