"""Token de Hugging Face del usuario: se guarda en la base y la API nunca lo devuelve (spec 034, D-2)."""

from __future__ import annotations

import re
import sqlite3

from content_studio.db import settings as store

KEY = 'secret.huggingface.token'
TOKEN = re.compile(r'hf_[A-Za-z0-9]{20,}')


def valid_token(token: str) -> bool:
    """True si el texto tiene la forma de un token de Hugging Face (hf_ seguido de letras y números).

    >>> valid_token('hf_' + 'a' * 34)
    True
    >>> valid_token('abc')
    False
    """
    return TOKEN.fullmatch(token) is not None


def huggingface_token(conn: sqlite3.Connection) -> str | None:
    """Token guardado, o None si no hay ninguno. Lo leen el instalador y la API, que solo dice si existe."""
    value = store.get(conn, KEY)
    return value if isinstance(value, str) else None


def set_huggingface_token(conn: sqlite3.Connection, token: str) -> None:
    """Guarda el token; el formato se valida antes, en la ruta."""
    store.set_value(conn, KEY, token)


def clear_huggingface_token(conn: sqlite3.Connection) -> None:
    """Borra el token guardado."""
    conn.execute('DELETE FROM settings WHERE key = ?', (KEY,))
