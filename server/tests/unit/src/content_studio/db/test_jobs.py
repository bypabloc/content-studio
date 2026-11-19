"""Tabla `jobs` (spec 004, D-1 y D-3): alta, lectura, filtros, siguiente en cola y actualización."""

from __future__ import annotations

import pytest

from content_studio.db import connection, jobs, schema


@pytest.fixture
def conn(tmp_path):
    db = connection.connect(tmp_path / 'base.db')
    schema.migrate(db)
    yield db
    db.close()


def test_insert_returns_an_id_and_get_decodes_params(conn):
    job_id = jobs.insert(conn, 'music', 'gpu', {'model': 'acestep', 'duration': 15})

    job = jobs.get(conn, job_id)

    assert job['status'] == 'queued'
    assert job['params'] == {'model': 'acestep', 'duration': 15}
    assert job['progress'] == 0


def test_positions_grow_and_next_queued_follows_them(conn):
    first = jobs.insert(conn, 'music', 'gpu', {})
    second = jobs.insert(conn, 'narration', 'gpu', {})

    assert jobs.next_queued(conn, 'gpu')['id'] == first
    assert jobs.get(conn, second)['position'] > jobs.get(conn, first)['position']


def test_next_queued_ignores_other_resources_and_finished_jobs(conn):
    cpu = jobs.insert(conn, 'convert', 'cpu', {})
    done = jobs.insert(conn, 'music', 'gpu', {})
    jobs.update(conn, done, status='done')

    assert jobs.next_queued(conn, 'gpu') is None
    assert jobs.next_queued(conn, 'cpu')['id'] == cpu


def test_update_changes_only_the_given_fields(conn):
    job_id = jobs.insert(conn, 'music', 'gpu', {})

    jobs.update(conn, job_id, status='running', progress=0.5, stage='block 1/2')

    job = jobs.get(conn, job_id)
    assert (job['status'], job['progress'], job['stage']) == ('running', 0.5, 'block 1/2')


def test_update_rejects_unknown_columns(conn):
    job_id = jobs.insert(conn, 'music', 'gpu', {})

    with pytest.raises(ValueError):
        jobs.update(conn, job_id, bogus=1)


def test_list_filters_by_status_and_kind(conn):
    music = jobs.insert(conn, 'music', 'gpu', {})
    jobs.insert(conn, 'narration', 'gpu', {})

    assert [job['id'] for job in jobs.list_jobs(conn, kind='music')] == [music]
    assert jobs.list_jobs(conn, status='done') == []


def test_get_missing_job_returns_none(conn):
    assert jobs.get(conn, 999) is None
