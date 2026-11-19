"""Trabajos de la API (spec 004, D-5, AC-7): 422 con code y message; alta, lista, cancelar y reintentar."""

from __future__ import annotations


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
