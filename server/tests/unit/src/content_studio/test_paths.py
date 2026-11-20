"""Rutas de almacenamiento elegibles de la spec 012."""

import os
from pathlib import Path

from content_studio import paths
from content_studio.db import settings
from content_studio.db.connection import connect
from content_studio.db.schema import migrate
from content_studio.narration.engines.registry import ENGINES


def test_ac1_defaults_outside_checkout(monkeypatch, tmp_path):
    """Los motores se guardan fuera del checkout incluso en desarrollo."""
    monkeypatch.delenv('CONTENT_STUDIO_HOME', raising=False)
    monkeypatch.delenv('CONTENT_STUDIO_MODE', raising=False)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(paths, 'ROOT', tmp_path / 'checkout')
    home = tmp_path / 'Content Studio' if os.name == 'nt' else tmp_path / '.local/share/content-studio'
    assert paths.engines_dir() == home / 'engines'
    assert paths.models_cache() == home / 'engines/hf'
    assert paths.outputs_dir() == paths.ROOT / 'out'
    assert paths.db_path() == paths.ROOT / 'var/content-studio.db'


def test_ac1_home_and_installed_mode(monkeypatch, tmp_path):
    """La instalación separa los modelos y la base de las salidas."""
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(tmp_path / 'app'))
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    assert paths.engines_dir() == tmp_path / 'app/engines'
    assert paths.models_cache() == tmp_path / 'app/engines/hf'
    assert paths.outputs_dir() == tmp_path / 'Documents/Content Studio'
    assert paths.db_path() == tmp_path / 'app/content-studio.db'


def test_ac1_settings_override_storage(monkeypatch, tmp_path):
    """Los settings de almacenamiento conservan la ubicación de SQLite."""
    database = tmp_path / 'db' / 'studio.db'
    monkeypatch.setenv('CONTENT_STUDIO_DB', str(database))
    conn = connect(database)
    try:
        migrate(conn)
        settings.set_value(conn, 'storage.engines', str(tmp_path / 'models'))
        settings.set_value(conn, 'storage.outputs', str(tmp_path / 'renders'))
    finally:
        conn.close()
    assert paths.engines_dir() == tmp_path / 'models'
    assert paths.models_cache() == tmp_path / 'models/hf'
    assert paths.outputs_dir() == tmp_path / 'renders'
    assert paths.db_path() == database


def test_ac1_managed_venv_has_priority_over_external_venv(monkeypatch, tmp_path):
    """El motor usa la instalación administrada si existe y conserva la externa en desarrollo."""
    external = tmp_path / 'legacy'
    home = tmp_path / 'studio'
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(home))
    monkeypatch.setenv('CONTENT_STUDIO_DB', str(tmp_path / 'base.db'))
    monkeypatch.delenv('CONTENT_STUDIO_MODE', raising=False)
    monkeypatch.setattr(paths, 'NARRATION', external)
    engine = ENGINES['qwen-0.6b']
    (external / engine.venv).mkdir(parents=True)
    assert engine.path_venv() == external / engine.venv

    managed = home / 'engines/narration' / engine.venv
    managed.mkdir(parents=True)
    assert engine.path_venv() == managed

    managed.rmdir()
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    assert engine.path_venv() == managed
