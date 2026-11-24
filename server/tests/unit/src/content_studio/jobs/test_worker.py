"""Worker de la cola (spec 004, D-3; AC-2, AC-3, AC-4, AC-11): orden, pausa, cancelación, candado y recuperación."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from content_studio import gpu_lock
from content_studio.db import connection, jobs, schema, subtitle_projects
from content_studio.jobs import queue
from content_studio.jobs.worker import Worker, stop_tree

# Proceso falso: anota en el log cuándo arranca y termina, duerme `sleep` segundos y emite un progreso.
SCRIPT = """
import json, sys, time
p = json.loads(sys.argv[1])
def mark(what):
    with open(p["log"], "a", encoding="utf-8") as f:
        f.write(f"{what} {p['label']} {time.time()}\\n")
mark("start")
time.sleep(p["sleep"])
print('@@progress {"p": 0.5, "stage": "half"}', flush=True)
mark("end")
"""


def _build(params: dict, out_dir: Path) -> list[str]:
    return [sys.executable, '-c', SCRIPT, json.dumps(params)]


def _service(resource: str) -> SimpleNamespace:
    return SimpleNamespace(RESOURCE=resource, validate=lambda params: [], build_command=_build)


@pytest.fixture
def env(tmp_path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    services = {'gpu_fake': _service('gpu'), 'cpu_fake': _service('cpu')}
    worker = Worker(
        tmp_path / 'base.db',
        main=tmp_path,
        services=services,
        out_root=tmp_path / 'out',
        log_dir=tmp_path / 'logs',
        poll=0.02,
    )
    yield SimpleNamespace(conn=conn, worker=worker, services=services, log=tmp_path / 'run.log', main=tmp_path)
    worker.stop()
    for job in jobs.list_jobs(conn, status='running'):
        worker.cancel(job['id'])
    conn.close()


def _enqueue(env, label: str, sleep: float = 0.1, kind: str = 'gpu_fake') -> int:
    return queue.enqueue(env.conn, kind, {'label': label, 'sleep': sleep, 'log': str(env.log)}, env.services)


def _wait_for(predicate, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def _marks(env) -> list[list[str]]:
    if not env.log.exists():
        return []
    return [line.split() for line in env.log.read_text(encoding='utf-8').splitlines()]


def _spans(env) -> dict[str, tuple[float, float]]:
    times: dict[str, dict[str, float]] = {}
    for what, label, when in _marks(env):
        times.setdefault(label, {})[what] = float(when)
    return {label: (t['start'], t['end']) for label, t in times.items()}


def test_stop_tree_falls_back_to_the_process_handle_when_taskkill_is_denied(monkeypatch):
    """El handle abierto por Popen todavía puede terminar el proceso si taskkill no tiene permiso."""
    monkeypatch.setattr(sys, 'platform', 'win32')
    process = SimpleNamespace(pid=123, killed=False, waited=False)
    process.kill = lambda: setattr(process, 'killed', True)
    process.wait = lambda: setattr(process, 'waited', True)
    monkeypatch.setattr(
        'content_studio.jobs.worker.subprocess.run',
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )

    stop_tree(process)

    assert process.killed
    assert process.waited


def test_ac2_paused_queue_runs_nothing_and_resume_follows_the_new_order(env):
    ids = [_enqueue(env, label) for label in ('1', '2', '3')]
    queue.reorder(env.conn, [ids[2], ids[0], ids[1]])
    queue.pause(env.conn)
    env.worker.start()

    time.sleep(0.3)
    assert [jobs.get(env.conn, i)['status'] for i in ids] == ['queued'] * 3

    queue.resume(env.conn)
    assert _wait_for(lambda: all(jobs.get(env.conn, i)['status'] == 'done' for i in ids))
    assert [label for what, label, _ in _marks(env) if what == 'start'] == ['3', '1', '2']
    assert Path(jobs.get(env.conn, ids[2])['output_dir'], 'params.json').is_file()


def test_ac2_a_queued_job_cancelled_before_it_runs_never_starts(env):
    first = _enqueue(env, 'a')
    second = _enqueue(env, 'b')
    queue.pause(env.conn)
    env.worker.start()

    assert env.worker.cancel(second)
    queue.resume(env.conn)

    assert _wait_for(lambda: jobs.get(env.conn, first)['status'] == 'done')
    assert jobs.get(env.conn, second)['status'] == 'cancelled'
    assert 'b' not in [label for _, label, _ in _marks(env)]


def test_ac3_cancelling_a_running_gpu_job_stops_it_frees_the_lock_and_retry_keeps_params(env):
    job = _enqueue(env, 'long', sleep=60)
    env.worker.start()
    assert _wait_for(lambda: jobs.get(env.conn, job)['status'] == 'running')

    started = time.monotonic()
    assert env.worker.cancel(job)
    assert _wait_for(lambda: not gpu_lock.lock(env.main).exists(), timeout=6)
    assert time.monotonic() - started < 6
    assert jobs.get(env.conn, job)['status'] == 'cancelled'

    queue.pause(env.conn)  # sin pausa, el worker arrancaría el reintento y dejaría el proceso de 60 s corriendo
    retried = queue.retry(env.conn, job)
    assert jobs.get(env.conn, retried)['params'] == jobs.get(env.conn, job)['params']


def test_ac4_gpu_jobs_never_overlap_and_a_cpu_job_runs_alongside(env):
    _enqueue(env, 'g1', sleep=0.6)
    _enqueue(env, 'g2', sleep=0.6)
    _enqueue(env, 'c', sleep=1.0, kind='cpu_fake')
    env.worker.start()
    assert _wait_for(lambda: all(job['status'] == 'done' for job in jobs.list_jobs(env.conn)))

    spans = _spans(env)
    (s1, e1), (s2, e2) = spans['g1'], spans['g2']
    assert e1 <= s2 or e2 <= s1
    cs, ce = spans['c']
    assert any(cs < end and start < ce for start, end in ((s1, e1), (s2, e2)))


def test_ac11_a_job_left_running_by_a_crash_becomes_an_interrupted_error(env):
    job = jobs.insert(env.conn, 'gpu_fake', 'gpu', {'label': 'x', 'sleep': 0, 'log': str(env.log)})
    jobs.update(env.conn, job, status='running')

    env.worker.start()

    row = jobs.get(env.conn, job)
    assert (row['status'], row['error_code']) == ('error', 'interrupted')


def test_run_now_runs_one_job_in_this_process_and_returns_its_final_status(env):
    job = _enqueue(env, 'solo', sleep=0.05)

    assert env.worker.run_now(job) == 'done'
    assert Path(jobs.get(env.conn, job)['output_dir'], 'params.json').is_file()


def test_editor_render_failure_keeps_structured_missing_source_paths(env):
    """El job conserva el detalle estructurado del render para mostrar las fuentes faltantes."""
    payload = {'status': 'failed', 'error': 'missing_source', 'params': {'paths': ['media/tono.wav']}}
    script = (
        'import pathlib, sys; '
        'pathlib.Path(sys.argv[1], "result.json").write_text(sys.argv[2], encoding="utf-8"); '
        'sys.exit(3)'
    )
    env.services['editor.render'] = SimpleNamespace(
        RESOURCE='cpu',
        ERROR_CODES={3: 'missing_source'},
        validate=lambda params: [],
        build_command=lambda params, out_dir: [
            sys.executable,
            '-c',
            script,
            str(out_dir),
            json.dumps(payload),
        ],
    )
    job = queue.enqueue(env.conn, 'editor.render', {'doc': 'project.json'}, env.services)

    assert env.worker.run_now(job) == 'error'

    row = jobs.get(env.conn, job)
    assert row['error_code'] == 'missing_source'
    assert json.loads(row['error_detail']) == payload


def test_auto_render_queues_the_render_when_the_analysis_ends(env):
    env.services['clean.analyze'] = _service('cpu')
    env.services['clean.render'] = _service('cpu')
    params = {'input': 'charla.mp4', 'auto_render': True, 'label': 'analisis', 'sleep': 0, 'log': str(env.log)}
    analysis = queue.enqueue(env.conn, 'clean.analyze', params, env.services)

    assert env.worker.run_now(analysis) == 'done'

    [render] = jobs.list_jobs(env.conn, kind='clean.render')
    assert render['status'] == 'queued'
    assert render['params'] == {'input': 'charla.mp4', 'analysis': jobs.get(env.conn, analysis)['output_dir']}


def test_without_auto_render_the_analysis_queues_no_render(env):
    env.services['clean.analyze'] = _service('cpu')
    env.services['clean.render'] = _service('cpu')
    params = {'input': 'charla.mp4', 'label': 'analisis', 'sleep': 0, 'log': str(env.log)}
    analysis = queue.enqueue(env.conn, 'clean.analyze', params, env.services)

    assert env.worker.run_now(analysis) == 'done'

    assert jobs.list_jobs(env.conn, kind='clean.render') == []


def test_a_done_subtitles_job_registers_its_project(env):
    """Al terminar `subtitles.create`, su documento queda como proyecto con el nombre del video (spec 014, D-1)."""
    script = (
        'import json, pathlib, sys\n'
        "doc = {'version': 1, 'source': {'path': 'charla.mp4', 'kind': 'file'}, 'language': 'es', 'cues': []}\n"
        "pathlib.Path(sys.argv[1], 'subtitles.json').write_text(json.dumps(doc), encoding='utf-8')\n"
    )
    env.services['subtitles.create'] = SimpleNamespace(
        RESOURCE='gpu',
        validate=lambda params: [],
        build_command=lambda params, out_dir: [sys.executable, '-c', script, str(out_dir)],
    )
    job = queue.enqueue(env.conn, 'subtitles.create', {'origin': 'file', 'input': 'charla.mp4'}, env.services)

    assert env.worker.run_now(job) == 'done'

    [project] = subtitle_projects.list_projects(env.conn)
    assert (project['name'], project['source_path']) == ('charla', 'charla.mp4')
    assert project['doc_path'] == str(Path(jobs.get(env.conn, job)['output_dir']) / 'subtitles.json')


def test_a_done_job_registers_its_outputs_in_the_library(env):
    """Spec 020, AC-1: al terminar, el worker deja las salidas del trabajo en `library_items`."""
    script = "import pathlib, sys; pathlib.Path(sys.argv[1], 'cut.srt').write_text('', encoding='utf-8')"
    env.services['media.trim'] = SimpleNamespace(
        RESOURCE='cpu',
        validate=lambda params: [],
        build_command=lambda params, out_dir: [sys.executable, '-c', script, str(out_dir)],
    )
    job = queue.enqueue(env.conn, 'media.trim', {'input': 'a.wav'}, env.services)

    assert env.worker.run_now(job) == 'done'

    [row] = env.conn.execute('SELECT kind, origin, job_id FROM library_items').fetchall()
    assert tuple(row) == ('trim', 'job', job)


def test_a_cancel_written_only_to_the_database_stops_a_running_process(env):
    job = _enqueue(env, 'long', sleep=60)
    env.worker.start()
    assert _wait_for(lambda: jobs.get(env.conn, job)['status'] == 'running')

    queue.cancel(env.conn, job)  # cancelado desde otro proceso: el worker lo ve en la base y termina el proceso

    assert _wait_for(lambda: not gpu_lock.lock(env.main).exists(), timeout=6)
    assert jobs.get(env.conn, job)['status'] == 'cancelled'
