"""Rutas de etiquetas y proyectos de la biblioteca (spec 020, D-3 y AC-8)."""

from __future__ import annotations

from contextlib import closing

from content_studio.db import connection
from content_studio.db.connection import utc_now


def _item(api, path: str) -> int:
    with closing(connection.connect(api.tmp / 'base.db')) as conn:
        return conn.execute(
            'INSERT INTO library_items (path, kind, origin, size, mtime, media_type, indexed_at) '
            "VALUES (?, 'music', 'watched', 1, 1, 'audio', ?)",
            (path, utc_now()),
        ).lastrowid


def test_ac8_tag_project_and_filter_through_the_api(api):
    """AC-8: etiquetar «reel 12», agregar a un proyecto y filtrar por los dos deja solo ese ítem."""
    item, _other = _item(api, '/a/uno.wav'), _item(api, '/a/dos.wav')
    h = api.headers

    tagged = api.client.post(f'/library/{item}/tags', json={'name': 'reel 12'}, headers=h)
    project = api.client.post('/projects', json={'name': 'Curso'}, headers=h).json()
    added = api.client.post(f'/projects/{project["id"]}/items', json={'items': [item]}, headers=h)
    found = api.client.get(f'/library?tag=reel 12&project={project["id"]}', headers=h).json()

    assert tagged.json() == ['reel 12']
    assert added.status_code == 204
    assert [i['name'] for i in found['items']] == ['uno.wav']
    assert api.client.get('/tags', headers=h).json() == [{'name': 'reel 12', 'count': 1}]
    assert [p['count'] for p in api.client.get('/projects', headers=h).json()] == [1]


def test_untag_rename_remove_and_delete(api):
    """DELETE de etiqueta, PATCH de proyecto, DELETE de ítem y de proyecto; lo que no existe da 404 o 422."""
    item = _item(api, '/a/uno.wav')
    h = api.headers
    api.client.post(f'/library/{item}/tags', json={'name': 'reel'}, headers=h)
    project = api.client.post('/projects', json={'name': 'Curso'}, headers=h).json()
    api.client.post(f'/projects/{project["id"]}/items', json={'items': [item]}, headers=h)

    untagged = api.client.delete(f'/library/{item}/tags?name=reel', headers=h)
    renamed = api.client.patch(f'/projects/{project["id"]}', json={'name': 'Curso 2'}, headers=h)
    removed = api.client.delete(f'/projects/{project["id"]}/items/{item}', headers=h)
    deleted = api.client.delete(f'/projects/{project["id"]}', headers=h)
    again = api.client.delete(f'/projects/{project["id"]}', headers=h)
    bad_tag = api.client.post('/library/999/tags', json={'name': 'x'}, headers=h)
    bad_name = api.client.post('/projects', json={'name': ' '}, headers=h)
    other = api.client.post('/projects', json={'name': 'Otro'}, headers=h).json()
    bad_item = api.client.post(f'/projects/{other["id"]}/items', json={'items': [999]}, headers=h)

    assert (untagged.json(), renamed.json()['name']) == ([], 'Curso 2')
    assert (removed.status_code, deleted.status_code) == (204, 204)
    assert (again.status_code, again.json()['code']) == (404, 'project_not_found')
    assert (bad_tag.status_code, bad_tag.json()['code']) == (404, 'item_not_found')
    assert (bad_name.status_code, bad_name.json()['code']) == (422, 'invalid_name')
    assert (bad_item.status_code, bad_item.json()['params']) == (404, {'item_id': 999})
