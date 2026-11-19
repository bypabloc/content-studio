"""Cliente de la API para las pruebas: base temporal, token fijo y los servicios reales más uno falso."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from content_studio.api.app import create_app
from content_studio.services.registry import SERVICES

TOKEN = 't-test'


@pytest.fixture
def api(tmp_path: Path) -> SimpleNamespace:
    """Cliente con el token de prueba; `headers` ya trae el Bearer. Sin worker: las rutas no ejecutan nada."""
    fake = SimpleNamespace(RESOURCE='gpu', validate=lambda params: [], build_command=lambda params, out: [])
    app = create_app(tmp_path / 'base.db', TOKEN, services={**SERVICES, 'fake': fake}, roots=[tmp_path / 'out'])
    return SimpleNamespace(
        client=TestClient(app),
        headers={'Authorization': f'Bearer {TOKEN}'},
        token=TOKEN,
        tmp=tmp_path,
    )
