"""Guarda de los parámetros que llegan de la red local (spec 032, D-2 y AC-6).

Un dispositivo solo pide tipos de contenido y solo nombra archivos como `upload:<id>` de sus propias subidas: cualquier
valor que parezca una ruta de esta PC se rechaza.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from content_studio.api.errors import ApiError
from content_studio.db.connection import utc_now
from content_studio.inbox.inputs import INPUT_PARAM

REMOTE_KINDS = frozenset({'narration', 'music', *INPUT_PARAM})
PATH_KEYS = frozenset(INPUT_PARAM.values())
PREFIX = 'upload:'
_PATHLIKE = re.compile(r'^(?:[A-Za-z]:[\\/]|[\\/]|~|\.{1,2}[\\/])')
_UNSAFE = re.compile(r'[^\w.-]+')


def looks_like_path(value: str) -> bool:
    """¿Parece una ruta de esta PC? Absoluta, de red, del usuario o relativa con `./` o `../`.

    >>> [looks_like_path(v) for v in ('C:/a.wav', '/etc/passwd', '~/a', '../a', 'Hola, mundo.', '1/2')]
    [True, True, True, True, False, False]
    """
    return bool(_PATHLIKE.match(value))


def safe_name(name: str) -> str:
    """El nombre del archivo subido sin carpetas ni caracteres raros (lo demás pasa a `_`)."""
    base = re.split(r'[\\/]', name)[-1]
    cleaned = _UNSAFE.sub('_', base).strip('._')
    return cleaned or 'upload'


def record_upload(conn: sqlite3.Connection, client_id: int, path: Path, size: int) -> int:
    """Anota una subida del dispositivo y devuelve su id."""
    cursor = conn.execute(
        'INSERT INTO uploads (client_id, path, size, created_at) VALUES (?, ?, ?, ?)',
        (client_id, str(path), size, utc_now()),
    )
    assert cursor.lastrowid is not None  # un INSERT siempre deja el id de la fila
    return cursor.lastrowid


def remote_params(conn: sqlite3.Connection, client_id: int, kind: str, params: dict[str, Any]) -> dict[str, Any]:
    """Los parámetros con cada `upload:<id>` cambiado por su ruta; 403 si el tipo o una ruta no se permiten."""
    if kind not in REMOTE_KINDS:
        raise ApiError(403, 'kind_not_allowed_remote', kind=kind)
    return {key: _value(conn, client_id, key, value) for key, value in params.items()}


def _value(conn: sqlite3.Connection, client_id: int, key: str, value: Any) -> Any:
    if isinstance(value, list):
        return [_value(conn, client_id, key, item) for item in value]
    if isinstance(value, dict):
        return {inner: _value(conn, client_id, inner, item) for inner, item in value.items()}
    if not isinstance(value, str):
        return value
    if value.startswith(PREFIX):
        return _upload_path(conn, client_id, value.removeprefix(PREFIX))
    if key in PATH_KEYS or looks_like_path(value):
        raise ApiError(403, 'remote_path_not_allowed')
    return value


def _upload_path(conn: sqlite3.Connection, client_id: int, upload_id: str) -> str:
    row = None
    if upload_id.isdigit():
        row = conn.execute(
            'SELECT path FROM uploads WHERE id = ? AND client_id = ?', (int(upload_id), client_id)
        ).fetchone()
    if row is None:
        raise ApiError(404, 'upload_not_found', upload=upload_id)
    return row['path']
