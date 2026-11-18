from __future__ import annotations

import sys

import pytest

# Lo que solo existe en los venvs de los motores. La capa liviana (parsers, catálogos, --help) no puede importarlo.
PESADAS = ['torch', 'torchaudio', 'numpy', 'soundfile', 'transformers', 'whisper', 'acestep', 'heartlib']


@pytest.fixture
def sin_pesadas(monkeypatch):
    """Hace fallar cualquier `import` de las dependencias pesadas mientras dura el test."""
    for nombre in PESADAS:
        monkeypatch.setitem(sys.modules, nombre, None)
