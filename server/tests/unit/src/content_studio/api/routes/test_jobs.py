"""Trabajos de la API (spec 004, D-5, AC-7): 422 con code y message; alta, lista, cancelar y reintentar."""

from __future__ import annotations

from contextlib import closing

from content_studio.db import connection, jobs


def test_ac7_an_unknown_engine_is_422_with_code_and_message(api):
    body = {'kind': 'narration', 'params': {'model': 'nope', 'style': 'expert', 'text': 'Hola.'}}

    response = api.client.post('/jobs', json=body, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'unknown_engine'
    assert 'nope' in response.json()['message']


def test_an_unknown_kind_is_422(api):
    response = api.client.post('/jobs', json={'kind': 'nope', 'params': {}}, headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'unknown_kind'


def test_a_valid_job_is_created_queued_and_listed(api):
    created = api.client.post('/jobs', json={'kind': 'fake', 'params': {'x': 1}}, headers=api.headers)
    job_id = created.json()['id']

    listed = api.client.get('/jobs', params={'kind': 'fake'}, headers=api.headers).json()

    assert created.status_code == 201
    assert (created.json()['status'], created.json()['resource']) == ('queued', 'gpu')
    assert [job['id'] for job in listed] == [job_id]


def test_a_missing_job_is_404(api):
    assert api.client.get('/jobs/999', headers=api.headers).json()['code'] == 'job_not_found'


def test_cancel_and_retry_follow_the_queue_rules(api):
    job_id = api.client.post('/jobs', json={'kind': 'fake', 'params': {'x': 1}}, headers=api.headers).json()['id']

    retry_pending = api.client.post(f'/jobs/{job_id}/retry', headers=api.headers)
    cancelled = api.client.post(f'/jobs/{job_id}/cancel', headers=api.headers)

    assert retry_pending.status_code == 409
    assert retry_pending.json()['code'] == 'job_pending'
    assert cancelled.json() == {'cancelled': True}


def test_a_job_id_beyond_sqlite_is_422_not_500(api):
    assert api.client.get('/jobs/99999999999999999999', headers=api.headers).status_code == 422


def test_star_refuses_a_job_that_is_not_a_finished_take(api):
    """Solo una toma terminada de narración se puede elegir: un trabajo en cola o de otro tipo, no."""
    job_id = api.client.post('/jobs', json={'kind': 'fake', 'params': {'x': 1}}, headers=api.headers).json()['id']

    response = api.client.post(f'/jobs/{job_id}/star', headers=api.headers)

    assert response.status_code == 409
    assert response.json()['code'] == 'job_not_a_take'


def test_ac5_star_is_unique_per_group(api):
    """AC-5: marcar una toma la deja como la única elegida de su grupo; las de otro grupo no cambian."""
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        first, second, other = (
            jobs.insert(conn, 'narration', 'gpu', {}, group_key=group)
            for group in ('narration:g1', 'narration:g1', 'narration:g2')
        )
        for job_id in (first, second, other):
            jobs.update(conn, job_id, status='done')
    for job_id in (first, other, second):
        api.client.post(f'/jobs/{job_id}/star', headers=api.headers)

    group = api.client.get('/jobs', params={'group_key': 'narration:g1'}, headers=api.headers).json()

    assert [(job['id'], job['starred']) for job in group] == [(first, False), (second, True)]
    assert api.client.get(f'/jobs/{other}', headers=api.headers).json()['starred'] is True


def test_a_retry_keeps_the_group_of_the_take(api):
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        job_id = jobs.insert(conn, 'fake', 'gpu', {}, group_key='narration:g1')
        jobs.update(conn, job_id, status='done')

    new = api.client.post(f'/jobs/{job_id}/retry', headers=api.headers).json()

    assert new['group_key'] == 'narration:g1'
