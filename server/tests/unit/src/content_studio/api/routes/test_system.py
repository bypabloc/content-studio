"""API de sistema sin cargar modelos ni instalar programas."""

from content_studio.system import tools


def test_ac6_get_system_reports_the_detected_tools(api, monkeypatch):
    """El estado mostrado por la app viene de la detección actual."""
    status = {'ffmpeg': {'path': 'ffmpeg', 'version': '8.0'}, 'git': None, 'gpu': None}
    monkeypatch.setattr(tools, 'detect', lambda: status)

    response = api.client.get('/system', headers=api.headers)

    assert response.status_code == 200
    assert response.json() == status


def test_ac6_winget_available_enqueues_the_tool_install(api, monkeypatch):
    """El endpoint encola un trabajo de CPU."""
    monkeypatch.setattr(tools, 'winget_path', lambda: 'winget')

    response = api.client.post('/system/tools/git/install', headers=api.headers)

    assert response.status_code == 201
    assert response.json()['kind'] == 'system.install_tool'
    assert response.json()['resource'] == 'cpu'
    assert response.json()['params'] == {'name': 'git'}


def test_ac6_no_winget_returns_installation_help(api, monkeypatch):
    """Sin instalador se indica cómo conseguir la herramienta."""
    monkeypatch.setattr(tools, 'winget_path', lambda: None)

    response = api.client.post('/system/tools/ffmpeg/install', headers=api.headers)

    assert response.status_code == 503
    assert response.json()['code'] == 'tool_install_failed'
    assert 'ffmpeg.org' in response.json()['message']


def test_ac6_rejects_unknown_tools(api):
    """No se aceptan nombres de paquetes en la ruta."""
    response = api.client.post('/system/tools/other/install', headers=api.headers)

    assert response.status_code == 422
    assert response.json()['code'] == 'unknown_system_tool'
