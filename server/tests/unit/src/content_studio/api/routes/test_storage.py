"""API de almacenamiento y compatibilidad de enlaces de trabajos anteriores."""

from contextlib import closing

from fastapi.testclient import TestClient

from content_studio import paths
from content_studio.api.app import create_app
from content_studio.db import connection, settings


def test_ac7_storage_exposes_its_roots_and_enqueues_a_move(api):
    """La API informa qué carpeta usa y encola el traslado al destino elegido."""
    result = api.client.get('/storage', headers=api.headers)
    assert result.status_code == 200
    assert result.json() == {'engines': str(paths.engines_dir()), 'outputs': str(paths.outputs_dir())}
    params = {'target': 'outputs', 'to': str(api.tmp / 'destination')}

    result = api.client.post('/storage/move', json=params, headers=api.headers)

    assert result.status_code == 201
    assert result.json()['kind'] == 'storage.move'
    assert result.json()['params'] == params


def test_ac7_rejects_relative_storage_destinations(api):
    """El destino solo se acepta como una ruta absoluta."""
    response = api.client.post('/storage/move', json={'target': 'engines', 'to': 'relative'}, headers=api.headers)
    assert response.status_code == 422
    assert response.json()['code'] == 'invalid_storage_destination'


def test_ac7_serves_old_output_paths_after_a_move(tmp_path):
    """La API atiende rutas emitidas antes del traslado y sigue limitando las carpetas servidas."""
    database = tmp_path / 'db.sqlite'
    app = create_app(database, 'token')
    original = tmp_path / 'before'
    current = tmp_path / 'after'
    current.mkdir()
    (current / 'track.wav').write_bytes(b'RIFF')
    with closing(connection.connect(database)) as conn:
        settings.set_value(conn, 'storage.outputs', str(current))
        settings.set_value(conn, 'storage.outputs_moves', {str(original): str(current)})
    client = TestClient(app)
    headers = {'Authorization': 'Bearer token'}

    assert client.get('/files', params={'path': str(original / 'track.wav')}, headers=headers).content == b'RIFF'
    assert client.get('/files', params={'path': str(current / 'track.wav')}, headers=headers).content == b'RIFF'
    assert client.get('/files', params={'path': str(database)}, headers=headers).status_code == 403
