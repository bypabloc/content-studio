"""Spec 028, AC-6: POST /server/stop pide el apagado con el token; sin token responde 401."""

from fastapi.testclient import TestClient

from content_studio.api.app import create_app


def test_stop_requests_shutdown_with_token(tmp_path):
    app = create_app(tmp_path / 'base.db', 'secret')
    asked: list[bool] = []
    app.state.stop = lambda: asked.append(True)
    client = TestClient(app)
    assert client.post('/server/stop').status_code == 401
    assert asked == []
    assert client.post('/server/stop', headers={'Authorization': 'Bearer secret'}).json() == {'stopping': True}
    assert asked == [True]
