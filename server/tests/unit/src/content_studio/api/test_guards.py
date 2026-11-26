"""Spec 028: guards del server compartido. AC-10: un Host ajeno recibe 400; el uso marca actividad, el sondeo no."""

from fastapi.testclient import TestClient

from content_studio.api.app import create_app
from content_studio.api.guards import ActivityGuard, HostGuard
from content_studio.runtime.idle import IdleClock

HOSTS = ['127.0.0.1', 'localhost']


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_ac10_foreign_host_gets_400(tmp_path):
    app = create_app(tmp_path / 'base.db', 'secret')
    headers = {'Authorization': 'Bearer secret'}
    foreign = TestClient(HostGuard(app, HOSTS), base_url='http://evil.example:41830')
    response = foreign.get('/health', headers=headers)
    assert response.status_code == 400
    assert response.json()['code'] == 'host_not_allowed'
    local = TestClient(HostGuard(app, HOSTS), base_url='http://127.0.0.1:41830')
    assert local.get('/health', headers=headers).status_code == 200


def test_activity_guard_marks_use_but_not_polling(tmp_path):
    clock = _FakeClock()
    idle = IdleClock(minutes=1, clock=clock)
    app = create_app(tmp_path / 'base.db', 'secret')
    client = TestClient(ActivityGuard(app, idle), base_url='http://127.0.0.1:41830')
    headers = {'Authorization': 'Bearer secret'}
    clock.now = 50
    client.get('/settings', headers=headers)
    clock.now = 61
    assert idle.idle() is False
    client.get('/health', headers=headers)
    clock.now = 115
    assert idle.idle() is True
