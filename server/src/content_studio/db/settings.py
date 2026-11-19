"""Tabla `settings` (spec 004, D-1): preferencias por clave, con valor JSON."""

from __future__ import annotations

import json
import sqlite3

from content_studio.db.connection import utc_now


def get(conn: sqlite3.Connection, key: str, default: object = None) -> object:
    """Valor de la clave, o `default` si no existe."""
    row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    return default if row is None else json.loads(row[0])


def set_value(conn: sqlite3.Connection, key: str, value: object) -> None:
    """Guarda o reemplaza la clave con un valor serializable en JSON."""
    conn.execute(
        'INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) '
        'ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at',
        (key, json.dumps(value), utc_now()),
    )


def all_values(conn: sqlite3.Connection) -> dict[str, object]:
    """Todas las preferencias como diccionario."""
    return {row[0]: json.loads(row[1]) for row in conn.execute('SELECT key, value FROM settings')}
