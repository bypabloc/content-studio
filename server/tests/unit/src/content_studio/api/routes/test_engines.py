"""API de motores administrados y externos, spec 012."""

from content_studio import paths
from content_studio.api.routes import engines


def test_ac5_rejects_external_uninstall_without_force(api, tmp_path, monkeypatch):
    """Un venv del checkout se identifica como externo y la API protege su instalación."""
    venv = tmp_path / 'external' / '.venv-qwen'
    venv.mkdir(parents=True)
    monkeypatch.setattr(paths, 'NARRATION', venv.parent)
    monkeypatch.delenv('CONTENT_STUDIO_MODE', raising=False)

    response = api.client.post('/engines/qwen-0.6b/uninstall', headers=api.headers)

    assert response.status_code == 409
    assert response.json()['code'] == 'engine_external'
    localized = api.client.post('/engines/qwen-0.6b/uninstall', headers={**api.headers, 'accept-language': 'en'})
    assert 'outside Content Studio' in localized.json()['message']
    entries = api.client.get('/engines', headers=api.headers).json()
    assert next(entry for entry in entries if entry['engine'] == 'qwen-0.6b')['status'] == 'external'


def test_noncommercial_install_needs_a_saved_license(api):
    """Aceptar la licencia habilita la instalación en la cola."""
    endpoint = '/engines/omnivoice/install'
    response = api.client.post(endpoint, headers={**api.headers, 'accept-language': 'en'})
    assert response.status_code == 409
    assert response.json()['code'] == 'engine_license_required'
    assert response.json()['message'] == 'Accept the engine license before installing it.'
    api.client.put('/settings/license.accepted.omnivoice', json={'value': True}, headers=api.headers)

    response = api.client.post(endpoint, headers=api.headers)
    assert response.status_code == 201
    assert response.json()['kind'] == 'engine.install'
    assert response.json()['params']['engine'] == 'omnivoice'


def test_unknown_engine_has_a_localized_404(api):
    response = api.client.post('/engines/not-a-motor/install', headers={**api.headers, 'accept-language': 'pt'})

    assert response.status_code == 404
    assert response.json()['code'] == 'unknown_engine'
    assert 'not-a-motor' in response.json()['message']
    assert response.json()['message'] != 'error.unknown_engine'


def test_owned_engine_uninstall_is_enqueued(api, tmp_path, monkeypatch):
    root = tmp_path / 'engines'
    home = root / 'qwen-0.6b'
    home.mkdir(parents=True)
    (home / 'install.json').write_text('{"owner": "app", "paths": ["qwen-0.6b"]}', encoding='utf-8')
    monkeypatch.setattr(engines, '_storage', lambda request: root)

    response = api.client.post('/engines/qwen-0.6b/uninstall', headers=api.headers)

    assert response.status_code == 201
    assert response.json()['kind'] == 'engine.uninstall'
    assert response.json()['params']['engine'] == 'qwen-0.6b'


def test_faster_whisper_lists_its_models_with_their_download_state(api, tmp_path, monkeypatch):
    """AC-9: GET /engines dice qué modelos de whisper hay, su tamaño y cuáles ya están descargados."""
    root = tmp_path / 'engines'
    snapshot = root / 'hf' / 'models--Systran--faster-whisper-small' / 'snapshots' / 'abc123'
    snapshot.mkdir(parents=True)
    (snapshot / 'model.bin').write_bytes(b'')
    monkeypatch.setattr(engines, '_storage', lambda request: root)

    entries = api.client.get('/engines', headers=api.headers).json()

    whisper = next(entry for entry in entries if entry['engine'] == 'faster-whisper')
    states = {model['model']: model['downloaded'] for model in whisper['models']}
    assert states == {'small': True, 'medium': False, 'large-v3-turbo': False, 'large-v3': False}
    assert next(model for model in whisper['models'] if model['recommended'])['model'] == 'large-v3-turbo'
    assert next(entry for entry in entries if entry['engine'] == 'qwen-0.6b')['models'] is None


def test_force_external_uninstall_is_explicitly_enqueued(api, tmp_path, monkeypatch):
    venv = tmp_path / 'external' / '.venv-qwen'
    venv.mkdir(parents=True)
    monkeypatch.setattr(paths, 'NARRATION', venv.parent)
    monkeypatch.delenv('CONTENT_STUDIO_MODE', raising=False)

    response = api.client.post('/engines/qwen-0.6b/uninstall?force=true', headers=api.headers)

    assert response.status_code == 201
    assert response.json()['params'] == {'engine': 'qwen-0.6b', 'force': True}


def test_verify_enqueues_a_gpu_job_only_for_an_installed_engine(api, tmp_path, monkeypatch):
    root = tmp_path / 'engines'
    venv = tmp_path / 'qwen-venv'
    venv.mkdir()
    monkeypatch.setattr(engines, '_storage', lambda request: root)
    monkeypatch.setattr(engines.installer, 'engine_venv', lambda recipe, storage: venv)

    response = api.client.post('/engines/qwen-0.6b/verify', headers=api.headers)

    assert response.status_code == 201
    assert response.json()['kind'] == 'engine.verify'
    assert response.json()['params']['engine'] == 'qwen-0.6b'


def test_verify_rejects_a_missing_engine(api, tmp_path, monkeypatch):
    monkeypatch.setattr(engines, '_storage', lambda request: tmp_path / 'engines')
    monkeypatch.setattr(engines.installer, 'engine_venv', lambda recipe, storage: tmp_path / 'missing-venv')

    response = api.client.post('/engines/qwen-0.6b/verify', headers=api.headers)

    assert response.status_code == 409
    assert response.json()['code'] == 'engine_not_installed'
