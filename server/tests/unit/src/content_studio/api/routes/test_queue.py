"""Cola de la API (spec 004, D-3 y D-5): pausar, reanudar y reordenar."""

from __future__ import annotations


def test_pause_and_resume_are_visible_in_get_queue(api):
    api.client.post('/queue/pause', headers=api.headers)
    assert api.client.get('/queue', headers=api.headers).json() == {'paused': True}

    api.client.post('/queue/resume', headers=api.headers)
    assert api.client.get('/queue', headers=api.headers).json() == {'paused': False}


def test_put_order_changes_the_position_of_the_jobs(api):
    first = api.client.post('/jobs', json={'kind': 'fake', 'params': {'n': 1}}, headers=api.headers).json()['id']
    second = api.client.post('/jobs', json={'kind': 'fake', 'params': {'n': 2}}, headers=api.headers).json()['id']

    response = api.client.put('/queue/order', json={'ids': [second, first]}, headers=api.headers)

    assert response.status_code == 200
    assert [job['id'] for job in api.client.get('/jobs', headers=api.headers).json()] == [second, first]
