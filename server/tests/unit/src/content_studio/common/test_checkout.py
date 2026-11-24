"""Checkout principal (spec 004, D-3): desde un worktree, la carpeta que contiene el .git común."""

from __future__ import annotations

from content_studio import paths
from content_studio.common.checkout import main_checkout


def test_main_checkout_holds_the_common_git_dir():
    assert (main_checkout(paths.ROOT) / '.git').exists()


def test_the_installed_app_keeps_the_gpu_turn_in_its_data_folder(monkeypatch, tmp_path):
    """Spec 022: la app instalada no es un checkout de git; el candado de la GPU vive en su carpeta de datos."""
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(tmp_path))

    assert main_checkout(tmp_path / 'no-es-un-repo') == tmp_path.resolve()
