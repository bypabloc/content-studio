from __future__ import annotations

import os
import sys

import pytest


@pytest.fixture(autouse=True)
def no_git_env(monkeypatch):
    """Dentro de un git hook (pre-commit), git exporta GIT_INDEX_FILE, GIT_DIR y compañía: los tests que crean repos
    temporales los heredarían y escribirían en el índice de este repo."""
    for name in [n for n in os.environ if n.startswith('GIT_')]:
        monkeypatch.delenv(name)


# Lo que solo existe en los venvs de los motores. La capa liviana (parsers, catálogos, --help) no puede importarlo.
HEAVY = ['torch', 'torchaudio', 'numpy', 'soundfile', 'transformers', 'whisper', 'acestep', 'heartlib']


@pytest.fixture
def no_heavy(monkeypatch):
    """Hace fallar cualquier `import` de las dependencias pesadas mientras dura el test."""
    for name in HEAVY:
        monkeypatch.setitem(sys.modules, name, None)
