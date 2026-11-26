"""Dispositivos de la red local (spec 032, D-3): un token por dispositivo, guardado como sha256 y revocable."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from collections.abc import Sequence

from content_studio.db.connection import utc_now

SCOPES = ('jobs', 'files')


def digest(token: str) -> str:
    """El sha256 del token en hexadecimal: lo único que se guarda.

    >>> len(digest('abc'))
    64
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create(conn: sqlite3.Connection, name: str, scopes: Sequence[str] = SCOPES) -> tuple[int, str]:
    """Da de alta un dispositivo y devuelve su id y su token en claro, que no se vuelve a mostrar."""
    token = secrets.token_urlsafe(32)
    cursor = conn.execute(
        'INSERT INTO api_clients (name, token_sha256, scopes, created_at) VALUES (?, ?, ?, ?)',
        (name, digest(token), ' '.join(scopes), utc_now()),
    )
    assert cursor.lastrowid is not None  # un INSERT siempre deja el id de la fila
    return cursor.lastrowid, token


def authenticate(conn: sqlite3.Connection, token: str) -> dict | None:
    """El dispositivo vigente con ese token (y anota que se vio), o None si no existe o se revocó."""
    if not token:
        return None
    row = conn.execute(
        'SELECT id, name, scopes FROM api_clients WHERE token_sha256 = ? AND revoked_at IS NULL', (digest(token),)
    ).fetchone()
    if row is None:
        return None
    conn.execute('UPDATE api_clients SET last_seen = ? WHERE id = ?', (utc_now(), row['id']))
    return {'id': row['id'], 'name': row['name'], 'scopes': row['scopes'].split()}


def revoke(conn: sqlite3.Connection, client_id: int) -> bool:
    """Revoca el dispositivo; False si no existe o ya estaba revocado."""
    cursor = conn.execute(
        'UPDATE api_clients SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL', (utc_now(), client_id)
    )
    return cursor.rowcount > 0


def list_clients(conn: sqlite3.Connection) -> list[dict]:
    """Los dispositivos vigentes, del más antiguo al más nuevo."""
    rows = conn.execute(
        'SELECT id, name, scopes, created_at, last_seen FROM api_clients WHERE revoked_at IS NULL ORDER BY id'
    )
    return [{**dict(row), 'scopes': row['scopes'].split()} for row in rows]
