from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def without_git_env(monkeypatch):
    """Dentro de un git hook (pre-commit), git exporta GIT_INDEX_FILE, GIT_DIR y compañía: los tests que crean repos
    temporales los heredarían y escribirían en el índice de este repo."""
    for name in [n for n in os.environ if n.startswith('GIT_')]:
        monkeypatch.delenv(name)
