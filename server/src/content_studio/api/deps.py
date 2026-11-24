"""Dependencias de las rutas: una conexión a la base por petición, cerrada al terminar (spec 004, D-5)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing

from fastapi import Request

from content_studio.db import connection


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    """Abre la base de la app para esta petición."""
    with closing(connection.connect(request.app.state.db_path)) as conn:
        yield conn
