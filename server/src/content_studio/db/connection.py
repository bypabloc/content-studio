"""Conexión a la base SQLite (spec 004, D-1): WAL, claves foráneas y espera de 5 s ante bloqueos."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    """Abre la base (y su carpeta si falta) en autocommit, con filas por nombre de columna."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Autocommit: las migraciones abren su propia transacción; el resto escribe de a una sentencia.
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


def utc_now() -> str:
    """Hora actual en UTC, ISO 8601 con segundos, para las columnas de tiempo."""
    return datetime.now(timezone.utc).isoformat(timespec='seconds')
