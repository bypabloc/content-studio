"""El LLM caliente en el worker, spec 021 AC-2: nunca dos modelos en la GPU y apagado por inactividad."""

from __future__ import annotations

import sys
import time
from types import SimpleNamespace

import pytest

from content_studio import gpu_lock
from content_studio.db import connection, jobs, schema, settings
from content_studio.jobs import queue
from content_studio.jobs.llm_warm import LlmWarm
from content_studio.jobs.worker import Worker
from content_studio.llm.client import LlmError


class FakeRuntime:
    """Runtime simulado: anota cuándo se carga y se apaga el modelo."""

    def __init__(self, events, fail=None):
        self.events = events
        self.model = None
        self.fail = fail

    @property
    def running(self):
        return self.model is not None

    def ensure_running(self, model):
        if self.fail:
            raise LlmError(self.fail)
        if self.model != model:
            self.events.append(f'load {model}')
        self.model = model
        return 'http://fake-llm'

    def stop(self):
        if self.model is not None:
            self.events.append('stop')
        self.model = None


@pytest.fixture
def env(tmp_path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    settings.set_value(conn, 'llm.idle_seconds', 0.6)
    events = []
    runtime = FakeRuntime(events)

    def service(name):
        def build(params, out_dir):
            # Al armar el comando, el trabajo ya tiene la GPU: se anota si el LLM seguía cargado.
            events.append(f'run {name} llm_loaded={runtime.running} url={params.get("llm_url")}')
            return [sys.executable, '-c', 'pass']

        return SimpleNamespace(RESOURCE='gpu', validate=lambda params: [], build_command=build)

    services = {'llm.music_caption': service('llm.music_caption'), 'narration': service('narration')}
    worker = Worker(
        tmp_path / 'base.db',
        main=tmp_path,
        services=services,
        out_root=tmp_path / 'out',
        log_dir=tmp_path / 'logs',
        poll=0.02,
        llm=LlmWarm(runtime),
    )
    yield SimpleNamespace(conn=conn, worker=worker, services=services, events=events, runtime=runtime, main=tmp_path)
    worker.stop()
    conn.close()


def _wait_for(predicate, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def _done(env, job_id):
    return jobs.get(env.conn, job_id)['status'] in ('done', 'error')


def test_ac2_the_llm_stops_before_another_gpu_job(env):
    """Un llm.* seguido de una narración: el LLM se apaga antes de que la narración arranque."""
    llm_id = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'piano'}, env.services)
    narration_id = queue.enqueue(env.conn, 'narration', {'text': 'hola'}, env.services)
    env.worker.start()

    assert _wait_for(lambda: _done(env, llm_id) and _done(env, narration_id))
    assert jobs.get(env.conn, narration_id)['status'] == 'done'
    assert env.events == [
        'load gemma-4-e4b',
        'run llm.music_caption llm_loaded=True url=http://fake-llm',
        'stop',
        'run narration llm_loaded=False url=None',
    ]


def test_ac2_consecutive_llm_jobs_reuse_the_warm_server_and_keep_the_turn(env):
    """Dos llm.* seguidos usan el mismo servidor; mientras está caliente, el candado sigue tomado."""
    first = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'a'}, env.services)
    env.worker.start()
    assert _wait_for(lambda: _done(env, first))
    assert gpu_lock.read(env.main) is not None  # caliente: el turno sigue siendo de este proceso
    second = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'b'}, env.services)

    assert _wait_for(lambda: _done(env, second))
    assert env.events.count('load gemma-4-e4b') == 1
    assert 'stop' not in env.events


def test_release_in_counts_down_while_warm(env):
    """Mientras está caliente, release_in dice cuánto falta para liberar la GPU; sin modelo, None."""
    job = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'a'}, env.services)
    env.worker.start()
    assert _wait_for(lambda: _done(env, job))
    assert _wait_for(lambda: env.worker.llm.release_in() is not None)

    assert 0 < env.worker.llm.release_in() <= 0.6
    assert _wait_for(lambda: env.worker.llm.release_in() is None)


def test_ac2_an_idle_server_stops_and_releases_the_turn(env):
    """Sin otro trabajo, a los idle_seconds se apaga el servidor y se suelta el candado de la GPU."""
    job = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'a'}, env.services)
    env.worker.start()
    assert _wait_for(lambda: _done(env, job))
    started = time.monotonic()

    assert _wait_for(lambda: 'stop' in env.events)
    assert time.monotonic() - started >= 0.3
    assert _wait_for(lambda: gpu_lock.read(env.main) is None)
    assert not env.runtime.running


def test_the_job_model_or_the_chosen_one_is_loaded(env):
    """El modelo sale de params.model o de la elección del usuario (select.llm.model)."""
    settings.set_value(env.conn, 'select.llm.model', 'qwen3.5-9b')
    job = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'a'}, env.services)
    env.worker.start()

    assert _wait_for(lambda: _done(env, job))
    assert env.events[0] == 'load qwen3.5-9b'


def test_a_runtime_error_ends_the_job_with_its_code(env):
    """Si el asistente no está instalado, el trabajo termina en error con llm_not_installed."""
    env.runtime.fail = 'llm_not_installed'
    job = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'a'}, env.services)
    env.worker.start()

    assert _wait_for(lambda: _done(env, job))
    row = jobs.get(env.conn, job)
    assert (row['status'], row['error_code']) == ('error', 'llm_not_installed')


def test_run_now_stops_the_llm_when_the_cli_job_ends(env):
    """Desde el CLI (run_now) no hay servidor caliente: se apaga al terminar el trabajo."""
    job = queue.enqueue(env.conn, 'llm.music_caption', {'description': 'a'}, env.services)

    assert env.worker.run_now(job) == 'done'
    assert env.events[-1] == 'stop'
    assert gpu_lock.read(env.main) is None
