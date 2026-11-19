"""Órdenes de la cola (spec 004, D-3): encolar, cancelar, reintentar, reordenar y pausar, sobre la base."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from content_studio.db import connection, jobs, schema
from content_studio.jobs import queue


@pytest.fixture
def conn(tmp_path):
    db = connection.connect(tmp_path / 'base.db')
    schema.migrate(db)
    yield db
    db.close()


def _service(resource='gpu', errors=()):
    return SimpleNamespace(RESOURCE=resource, validate=lambda params: list(errors))


def test_enqueue_takes_the_resource_of_the_service(conn):
    job_id = queue.enqueue(conn, 'fake', {'a': 1}, {'fake': _service('cpu')})

    assert jobs.get(conn, job_id)['resource'] == 'cpu'


def test_enqueue_rejects_invalid_params_with_their_errors(conn):
    errors = [{'code': 'unknown_style', 'params': {'style': 'x'}}]

    with pytest.raises(queue.InvalidJob) as raised:
        queue.enqueue(conn, 'fake', {}, {'fake': _service(errors=errors)})

    assert raised.value.errors == errors
    assert jobs.list_jobs(conn) == []


def test_cancel_only_applies_to_pending_or_running_jobs(conn):
    job_id = jobs.insert(conn, 'fake', 'gpu', {})

    assert queue.cancel(conn, job_id) is True
    assert jobs.get(conn, job_id)['status'] == 'cancelled'
    assert queue.cancel(conn, job_id) is False
    assert queue.cancel(conn, 999) is False


def test_retry_copies_params_into_a_new_queued_job(conn):
    old = jobs.insert(conn, 'fake', 'gpu', {'style': 'lofi-chill'})
    jobs.update(conn, old, status='error')

    new = queue.retry(conn, old)

    assert new != old
    assert jobs.get(conn, new)['params'] == {'style': 'lofi-chill'}
    assert jobs.get(conn, new)['status'] == 'queued'


def test_retry_refuses_a_job_that_is_still_pending(conn):
    job_id = jobs.insert(conn, 'fake', 'gpu', {})

    with pytest.raises(ValueError):
        queue.retry(conn, job_id)


def test_reorder_sets_the_given_order_and_the_pause_flag_round_trips(conn):
    ids = [jobs.insert(conn, 'fake', 'gpu', {}) for _ in range(3)]

    queue.reorder(conn, [ids[2], ids[0], ids[1]])

    assert jobs.next_queued(conn, 'gpu')['id'] == ids[2]
    assert not queue.paused(conn)
    queue.pause(conn)
    assert queue.paused(conn)
    queue.resume(conn)
    assert not queue.paused(conn)


def test_reorder_keeps_a_running_job_in_its_own_slot(conn):
    """Reordenar los que esperan no empata sus puestos con el trabajo en curso: cada uno ocupa el suyo."""
    running = jobs.insert(conn, 'fake', 'gpu', {})
    first = jobs.insert(conn, 'fake', 'gpu', {})
    second = jobs.insert(conn, 'fake', 'gpu', {})
    jobs.update(conn, running, status='running')

    queue.reorder(conn, [second, first])

    listed = jobs.list_jobs(conn)
    assert [job['id'] for job in listed] == [running, second, first]
    assert [job['position'] for job in listed] == [1, 2, 3]


def test_claim_moves_only_a_queued_job_to_running(conn):
    job_id = jobs.insert(conn, 'fake', 'gpu', {})

    assert queue.claim(conn, job_id) is True
    assert jobs.get(conn, job_id)['status'] == 'running'
    assert queue.claim(conn, job_id) is False  # otro actor ya lo tomó: no se corre dos veces


def test_claim_records_the_process_that_runs_the_job(conn):
    job_id = jobs.insert(conn, 'fake', 'gpu', {})

    queue.claim(conn, job_id)

    assert conn.execute('SELECT owner_pid FROM jobs WHERE id = ?', (job_id,)).fetchone()[0] == os.getpid()


def test_recover_keeps_a_running_job_whose_process_is_alive(conn):
    job_id = jobs.insert(conn, 'fake', 'gpu', {})
    queue.claim(conn, job_id)  # lo corre este proceso, que sigue vivo: el server no lo interrumpe

    assert queue.recover_interrupted(conn) == 0
    assert jobs.get(conn, job_id)['status'] == 'running'


def test_recover_interrupts_a_running_job_whose_process_is_gone(conn):
    job_id = jobs.insert(conn, 'fake', 'gpu', {})
    conn.execute("UPDATE jobs SET status = 'running', owner_pid = ? WHERE id = ?", (999_999, job_id))

    assert queue.recover_interrupted(conn) == 1
    row = jobs.get(conn, job_id)
    assert (row['status'], row['error_code']) == ('error', 'interrupted')
