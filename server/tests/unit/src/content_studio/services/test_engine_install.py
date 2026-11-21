"""Códigos de error de instalación de motores, AC-3 y AC-4 de la spec 012."""

import sys

from content_studio import paths
from content_studio.engines import installer
from content_studio.services import engine_install


def test_worker_exit_codes_keep_the_error_code():
    """El worker transforma el código de salida en un error localizable."""
    assert engine_install.ERROR_CODES[installer.EXIT_CODES['disk_full']] == 'disk_full'
    assert engine_install.ERROR_CODES[installer.EXIT_CODES['engine_external']] == 'engine_external'


def test_validate_requires_a_catalog_engine_and_boolean_repair():
    assert engine_install.validate({'engine': 'qwen-0.6b'}) == []
    assert engine_install.validate({'engine': 'unknown!'})[0]['code'] == 'unknown_engine'
    assert engine_install.validate({'engine': 'qwen-0.6b', 'repair': 'yes'})[0]['code'] == 'invalid_engine_action'


def test_build_command_includes_repair_only_when_requested(tmp_path):
    assert engine_install.build_command({'engine': 'qwen-0.6b'}, tmp_path) == [
        sys.executable,
        '-m',
        engine_install.__name__,
        'qwen-0.6b',
    ]
    assert engine_install.build_command({'engine': 'qwen-0.6b', 'repair': True}, tmp_path)[-1] == '--repair'


def test_run_checks_license_and_installs_in_the_configured_roots(monkeypatch, tmp_path):
    class Connection:
        def close(self):
            pass

    calls = []
    monkeypatch.setattr(engine_install.connection, 'connect', lambda path: Connection())
    monkeypatch.setattr(paths, 'db_path', lambda: tmp_path / 'db.sqlite')
    monkeypatch.setattr(paths, 'engines_dir', lambda: tmp_path / 'engines')
    monkeypatch.setattr(installer, 'check_license', lambda conn, engine: calls.append(('license', engine)))
    monkeypatch.setattr(installer, 'install', lambda recipe, root, repair: calls.append((recipe.engine, root, repair)))

    assert engine_install.run('qwen-0.6b', True) == 0
    assert calls == [('license', 'qwen-0.6b'), ('qwen-0.6b', tmp_path / 'engines', True)]


def test_run_returns_the_install_error_code_and_writes_it_to_stderr(monkeypatch, tmp_path, capsys):
    class Connection:
        def close(self):
            pass

    monkeypatch.setattr(engine_install.connection, 'connect', lambda path: Connection())
    monkeypatch.setattr(paths, 'db_path', lambda: tmp_path / 'db.sqlite')
    monkeypatch.setattr(
        installer,
        'check_license',
        lambda conn, engine: (_ for _ in ()).throw(installer.InstallError('engine_license_required')),
    )

    result = engine_install.run('omnivoice', False)

    assert result == installer.EXIT_CODES['engine_license_required']
    assert capsys.readouterr().err.strip() == 'engine_license_required'
