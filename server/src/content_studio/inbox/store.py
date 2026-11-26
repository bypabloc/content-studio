"""Carpetas de entrada y los archivos que tomaron (spec 030, 02 §3): altas, bajas, cambios y lecturas."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from content_studio.db.connection import utc_now
from content_studio.inbox import inputs
from content_studio.jobs import queue
from content_studio.services.registry import SERVICES

WORK_FOLDERS = ('processing', 'done', 'failed')
ITEM_FIELDS = frozenset({'state', 'job_id'})


class InboxError(ValueError):
    """Un error de carpeta de entrada con su código (`folder_not_found`, `unknown_kind`…) y sus parámetros."""

    def __init__(self, code: str, **params: Any) -> None:
        """Guarda el código y los parámetros para el mensaje."""
        super().__init__(code)
        self.code = code
        self.params: dict[str, Any] = params


def _folder(row: sqlite3.Row) -> dict[str, Any]:
    """Una carpeta con `params` decodificado y las banderas como booleanos."""
    folder = dict(row)
    folder['params'] = json.loads(folder['params'])
    folder['keep_awake'] = bool(folder['keep_awake'])
    folder['paused'] = bool(folder['paused'])
    return folder


def register(
    conn: sqlite3.Connection,
    path: str,
    kind: str,
    params: dict,
    keep_awake: bool = True,
    services: Mapping[str, Any] = SERVICES,
) -> int:
    """Registra una carpeta: debe existir, el tipo tiene que aceptar archivos y los parámetros pasar su validación."""
    folder = Path(path)
    if not folder.is_dir():
        raise InboxError('inbox_path_not_found', path=path)
    if kind not in services:
        raise InboxError('unknown_kind', kind=kind)
    if kind not in inputs.INPUT_PARAM:
        raise InboxError('inbox_kind_not_accepted', kind=kind)
    probe = {**params, inputs.INPUT_PARAM[kind]: inputs.input_value(kind, folder)}
    errors = services[kind].validate(probe)
    if errors:
        raise queue.InvalidJob(errors)
    try:
        cursor = conn.execute(
            'INSERT INTO inbox_folders (path, kind, params, keep_awake, paused, created_at) VALUES (?, ?, ?, ?, 0, ?)',
            (str(folder.resolve()), kind, json.dumps(params, ensure_ascii=False), int(keep_awake), utc_now()),
        )
    except sqlite3.IntegrityError as error:
        raise InboxError('inbox_folder_already_registered', path=path) from error
    for name in WORK_FOLDERS:
        (folder / name).mkdir(exist_ok=True)
    folder_id = cursor.lastrowid
    assert folder_id is not None  # un INSERT siempre deja el id de la fila
    return folder_id


def get(conn: sqlite3.Connection, folder_id: int) -> dict[str, Any] | None:
    """La carpeta `folder_id`, o None si no está registrada."""
    row = conn.execute('SELECT * FROM inbox_folders WHERE id = ?', (folder_id,)).fetchone()
    return None if row is None else _folder(row)


def list_folders(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Todas las carpetas registradas, en orden de alta."""
    return [_folder(row) for row in conn.execute('SELECT * FROM inbox_folders ORDER BY id')]


def remove(conn: sqlite3.Connection, folder_id: int) -> bool:
    """Quita la carpeta y su historial; los archivos del disco no se tocan. True si existía."""
    return conn.execute('DELETE FROM inbox_folders WHERE id = ?', (folder_id,)).rowcount == 1


def set_keep_awake(conn: sqlite3.Connection, folder_id: int, value: bool) -> None:
    """Cambia si la carpeta mantiene el server encendido."""
    conn.execute('UPDATE inbox_folders SET keep_awake = ? WHERE id = ?', (int(value), folder_id))


def set_paused(conn: sqlite3.Connection, folder_id: int, value: bool) -> None:
    """Pausa o reanuda el sondeo de la carpeta."""
    conn.execute('UPDATE inbox_folders SET paused = ? WHERE id = ?', (int(value), folder_id))


def add_item(
    conn: sqlite3.Connection, folder_id: int, name: str, size: int, mtime: float, state: str, job_id: int | None = None
) -> int:
    """Anota una versión vista de un archivo (tamaño y fecha) en `state`: pending, processing, done o failed."""
    cursor = conn.execute(
        'INSERT INTO inbox_items (folder_id, name, size, mtime, state, job_id) VALUES (?, ?, ?, ?, ?, ?)',
        (folder_id, name, size, mtime, state, job_id),
    )
    item_id = cursor.lastrowid
    assert item_id is not None  # un INSERT siempre deja el id de la fila
    return item_id


def find_item(conn: sqlite3.Connection, folder_id: int, name: str, size: int, mtime: float) -> dict[str, Any] | None:
    """La anotación de esa versión exacta del archivo (mismo tamaño y fecha), o None."""
    row = conn.execute(
        'SELECT * FROM inbox_items WHERE folder_id = ? AND name = ? AND size = ? AND mtime = ?',
        (folder_id, name, size, mtime),
    ).fetchone()
    return None if row is None else dict(row)


def drop_pending(conn: sqlite3.Connection, folder_id: int, name: str) -> None:
    """Olvida las versiones de `name` que aún esperan: el archivo cambió de tamaño o de fecha."""
    conn.execute("DELETE FROM inbox_items WHERE folder_id = ? AND name = ? AND state = 'pending'", (folder_id, name))


def update_item(conn: sqlite3.Connection, item_id: int, **fields: object) -> None:
    """Cambia `state` o `job_id` de un archivo; cualquier otra columna se rechaza."""
    unknown = set(fields) - ITEM_FIELDS
    if unknown:
        raise ValueError(f'non-editable columns: {sorted(unknown)}')
    if fields:
        assignments = ', '.join(f'{name} = ?' for name in fields)
        conn.execute(f'UPDATE inbox_items SET {assignments} WHERE id = ?', (*fields.values(), item_id))


def processing_items(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Los archivos tomados que ya tienen trabajo, con la ruta de su carpeta."""
    rows = conn.execute(
        'SELECT i.*, f.path AS path FROM inbox_items i JOIN inbox_folders f ON f.id = i.folder_id '
        "WHERE i.state = 'processing' AND i.job_id IS NOT NULL ORDER BY i.id"
    )
    return [dict(row) for row in rows]
