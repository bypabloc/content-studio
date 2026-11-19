from __future__ import annotations

import os
import sys

import pytest


@pytest.fixture(autouse=True)
def sin_entorno_git(monkeypatch):
    """Dentro de un git hook (pre-commit), git exporta GIT_INDEX_FILE, GIT_DIR y compañía: los tests que crean repos
    temporales los heredarían y escribirían en el índice de este repo."""
    for nombre in [n for n in os.environ if n.startswith('GIT_')]:
        monkeypatch.delenv(nombre)


# Lo que solo existe en los venvs de los motores. La capa liviana (parsers, catálogos, --help) no puede importarlo.
PESADAS = ['torch', 'torchaudio', 'numpy', 'soundfile', 'transformers', 'whisper', 'acestep', 'heartlib']


@pytest.fixture
def sin_pesadas(monkeypatch):
    """Hace fallar cualquier `import` de las dependencias pesadas mientras dura el test."""
    for nombre in PESADAS:
        monkeypatch.setitem(sys.modules, nombre, None)
