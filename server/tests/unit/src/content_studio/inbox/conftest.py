"""Fixtures de las pruebas de carpetas de entrada: una base migrada, una carpeta y un tipo falso que valida."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from content_studio.db import connection, schema


class FakeConvert:
    """Tipo de trabajo falso: el destino `bad` no pasa la validación y corre en la CPU."""

    RESOURCE = 'cpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        """Los errores de validación del tipo falso."""
        if params.get('target') == 'bad':
            return [{'code': 'unknown_target', 'params': {'target': 'bad'}}]
        return []


@pytest.fixture
def services() -> dict:
    """Solo el tipo falso: las pruebas no dependen de ffmpeg ni de los motores."""
    return {'media.convert': FakeConvert}


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Una base de SQLite migrada, en la carpeta temporal de la prueba."""
    path = tmp_path / 'content-studio.db'
    conn = connection.connect(path)
    schema.migrate(conn)
    conn.close()
    return path


@pytest.fixture
def conn(db_path: Path) -> Iterator[connection.sqlite3.Connection]:
    """Una conexión a la base de la prueba, cerrada al terminar."""
    handle = connection.connect(db_path)
    yield handle
    handle.close()


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """La carpeta de entrada de la prueba, ya creada."""
    path = tmp_path / 'entrada'
    path.mkdir()
    return path
