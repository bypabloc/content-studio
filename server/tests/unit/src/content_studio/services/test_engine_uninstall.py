"""Propiedad y rutas al desinstalar motores, AC-5 de la spec 012."""

import json
import sys

import pytest

from content_studio import paths
from content_studio.services import engine_uninstall


def test_ac5_external_installation_is_never_removed_by_default(tmp_path, monkeypatch):
    """Un venv externo conserva sus archivos aunque el usuario solicite desinstalarlo."""
    try:
        from content_studio.engines import installer
    except ImportError as error:
        pytest.fail(f'AC-5 requires installation ownership checks: {error}')
    external = tmp_path / 'external'
    venv = external / '.venv-qwen'
    venv.mkdir(parents=True)
    (venv / 'keep').write_bytes(b'owned by the user')
    monkeypatch.setattr(paths, 'NARRATION', external)
    monkeypatch.delenv('CONTENT_STUDIO_MODE', raising=False)

    with pytest.raises(installer.InstallError) as error:
        installer.uninstall('qwen-0.6b', tmp_path / 'engine data')

    assert error.value.code == 'engine_external'
    assert (venv / 'keep').read_bytes() == b'owned by the user'


def test_ac5_owned_installation_only_removes_its_listed_paths(tmp_path):
    """La instalación de al lado y cualquier otro archivo del usuario se conservan."""
    try:
        from content_studio.engines import installer
    except ImportError as error:
        pytest.fail(f'AC-5 requires the uninstaller: {error}')
    owned = tmp_path / 'qwen-0.6b'
    weights = tmp_path / 'hf' / 'qwen-0.6b'
    neighbor = tmp_path / 'qwen-1.7b'
    neighbor_weights = tmp_path / 'hf' / 'qwen-1.7b'
    for folder in (owned, weights, neighbor, neighbor_weights):
        folder.mkdir(parents=True)
        (folder / 'keep').write_bytes(b'marker')
    (owned / 'install.json').write_text(
        json.dumps({'owner': 'app', 'paths': ['qwen-0.6b', 'hf/qwen-0.6b']}), encoding='utf-8'
    )

    installer.uninstall('qwen-0.6b', tmp_path)

    assert not owned.exists()
    assert not weights.exists()
    assert (neighbor / 'keep').is_file()
    assert (neighbor_weights / 'keep').is_file()


def test_uninstall_service_validates_and_builds_a_command(tmp_path):
    assert engine_uninstall.validate({'engine': 'qwen-0.6b'}) == []
    assert engine_uninstall.validate({'engine': 'unknown!'})[0]['code'] == 'unknown_engine'
    assert engine_uninstall.build_command({'engine': 'qwen-0.6b'}, tmp_path) == [
        sys.executable,
        '-m',
        engine_uninstall.__name__,
        'qwen-0.6b',
    ]
    assert engine_uninstall.validate({'engine': 'qwen-0.6b', 'force': 'yes'})[0]['code'] == 'invalid_engine_action'
    assert engine_uninstall.build_command({'engine': 'qwen-0.6b', 'force': True}, tmp_path)[-1] == '--force'


def test_uninstall_service_returns_the_domain_error(monkeypatch, tmp_path, capsys):
    from content_studio.engines import installer

    monkeypatch.setattr(paths, 'engines_dir', lambda: tmp_path)

    def reject(engine, root, force=False):
        raise installer.InstallError('engine_external')

    monkeypatch.setattr(installer, 'uninstall', reject)

    assert engine_uninstall.run('qwen-0.6b') == installer.EXIT_CODES['engine_external']
    assert capsys.readouterr().err.strip() == 'engine_external'


def test_uninstall_service_passes_the_configured_root(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(paths, 'engines_dir', lambda: tmp_path)
    monkeypatch.setattr(
        engine_uninstall.installer, 'uninstall', lambda engine, root, force=False: calls.append((engine, root, force))
    )

    assert engine_uninstall.run('qwen-0.6b') == 0
    assert calls == [('qwen-0.6b', tmp_path, False)]


def test_uninstall_service_passes_force_to_the_installer(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(paths, 'engines_dir', lambda: tmp_path)
    monkeypatch.setattr(engine_uninstall.installer, 'uninstall', lambda *args, **kwargs: calls.append((args, kwargs)))

    assert engine_uninstall.run('qwen-0.6b', force=True) == 0
    assert calls == [(('qwen-0.6b', tmp_path), {'force': True})]
