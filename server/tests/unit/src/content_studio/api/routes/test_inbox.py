"""Spec 030, fase 2: la API de carpetas de entrada (AC-1): alta con validación, lista, pausa y baja."""

from fastapi.testclient import TestClient

from content_studio.api.app import create_app

TOKEN = 't-test'
HEADERS = {'Authorization': f'Bearer {TOKEN}'}


class FakeNormalize:
    """Tipo de trabajo falso: el preset `bad` no pasa la validación."""

    RESOURCE = 'cpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        if params.get('preset') == 'bad':
            return [{'code': 'unknown_preset', 'params': {'preset': 'bad'}}]
        return []


def test_ac1_post_get_pause_delete(tmp_path):
    folder = tmp_path / 'entrada'
    folder.mkdir()
    app = create_app(tmp_path / 'base.db', TOKEN, services={'media.normalize': FakeNormalize}, roots=[tmp_path / 'out'])
    client = TestClient(app)
    body = {'path': str(folder), 'kind': 'media.normalize', 'params': {'preset': 'ok'}}

    created = client.post('/inbox/folders', json=body, headers=HEADERS)
    assert created.status_code == 201
    folder_id = created.json()['id']
    assert created.json()['path'] == str(folder.resolve())
    assert created.json()['keep_awake'] is True
    assert [item['id'] for item in client.get('/inbox/folders', headers=HEADERS).json()] == [folder_id]

    missing = client.post('/inbox/folders', json={**body, 'path': str(tmp_path / 'no-existe')}, headers=HEADERS)
    assert missing.status_code == 422
    assert missing.json()['code'] == 'inbox_path_not_found'
    invalid = client.post('/inbox/folders', json={**body, 'params': {'preset': 'bad'}}, headers=HEADERS)
    assert invalid.status_code == 422
    assert invalid.json()['code'] == 'unknown_preset'

    paused = client.post(f'/inbox/folders/{folder_id}/pause', json={'paused': True}, headers=HEADERS)
    assert paused.status_code == 200
    assert paused.json()['paused'] is True
    assert client.delete(f'/inbox/folders/{folder_id}', headers=HEADERS).status_code == 204
    gone = client.delete(f'/inbox/folders/{folder_id}', headers=HEADERS)
    assert gone.status_code == 404
    assert gone.json()['code'] == 'inbox_folder_not_found'
