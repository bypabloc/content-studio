"""Acciones de la biblioteca (spec 020, D-4): origen, repetir, renombrar, mover y mandar a la papelera.

Nunca sobrescribe: si el destino existe, `FileExistsError`. Las rutas de las referencias de voz, las voces y los
motores están protegidas. La papelera es la de Windows (`send2trash`); quitar solo el registro no toca el archivo.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from content_studio import paths
from content_studio.db import jobs, settings
from content_studio.jobs import queue
from content_studio.library import scan


class ProtectedPath(Exception):
    """La ruta está en las referencias de voz, las voces o los motores: la Biblioteca no la toca."""


def protected_roots() -> list[Path]:
    """Carpetas que la Biblioteca no puede borrar, renombrar ni mover."""
    return [paths.references_dir(), paths.voices_dir(), paths.engines_dir()]


def send_to_trash(path: Path) -> None:
    """Manda el archivo o la carpeta a la papelera del sistema."""
    from send2trash import send2trash  # dependencia del server, solo al borrar

    send2trash(str(path))


def _item(conn: sqlite3.Connection, item_id: int) -> dict:
    row = conn.execute('SELECT * FROM library_items WHERE id = ?', (item_id,)).fetchone()
    if row is None:
        raise LookupError(item_id)
    return {**dict(row), 'name': Path(row['path']).name}


def check_unprotected(path: Path) -> None:
    """ProtectedPath si la ruta está en las referencias, las voces o los motores."""
    target = path.resolve()
    if any(target.is_relative_to(root.resolve()) for root in protected_roots()):
        raise ProtectedPath(str(path))


def _elapsed(job: dict) -> float | None:
    if not job.get('started_at') or not job.get('finished_at'):
        return None
    return (datetime.fromisoformat(job['finished_at']) - datetime.fromisoformat(job['started_at'])).total_seconds()


def origin(conn: sqlite3.Connection, item_id: int) -> dict:
    """El ítem, su trabajo (params, resultado, fechas y duración del proceso), sus otras salidas y las tomas."""
    item = _item(conn, item_id)
    job = jobs.get(conn, item['job_id']) if item['job_id'] else None
    outputs: list[dict] = []
    takes: list[dict] = []
    if job is not None:
        job = {**job, 'elapsed': _elapsed(job)}
        rows = conn.execute(
            'SELECT * FROM library_items WHERE job_id = ? AND id != ? ORDER BY path', (job['id'], item_id)
        )
        outputs = [dict(row) for row in rows]
        if job['group_key']:
            rows = conn.execute(
                'SELECT i.*, j.starred FROM library_items i JOIN jobs j ON j.id = i.job_id '
                'WHERE j.group_key = ? AND j.id != ? ORDER BY i.id',
                (job['group_key'], job['id']),
            )
            takes = [{**dict(row), 'starred': bool(row['starred'])} for row in rows]
    return {'item': item, 'job': job, 'outputs': outputs, 'takes': takes}


def repeat(conn: sqlite3.Connection, item_id: int) -> int:
    """Encola un trabajo nuevo con los mismos `params`. ValueError si el ítem no salió de un trabajo."""
    item = _item(conn, item_id)
    if not item['job_id']:
        raise ValueError('item has no job')
    return queue.retry(conn, item['job_id'])


def _replace(value: object, old: str, new: str) -> object:
    """Cambia en un JSON cada cadena igual a `old` por `new`."""
    if isinstance(value, str):
        return new if value == old else value
    if isinstance(value, list):
        return [_replace(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: _replace(item, old, new) for key, item in value.items()}
    return value


def _relocate(conn: sqlite3.Connection, item: dict, target: Path) -> dict:
    """Mueve el archivo sin sobrescribir y actualiza la ruta en el índice y en `jobs.result`."""
    source = Path(item['path'])
    check_unprotected(source)
    check_unprotected(target)
    if target.exists():
        raise FileExistsError(str(target))
    shutil.move(str(source), str(target))
    conn.execute(
        'UPDATE library_items SET path = ?, mtime = ? WHERE id = ?', (str(target), target.stat().st_mtime, item['id'])
    )
    if item['job_id']:
        result = conn.execute('SELECT result FROM jobs WHERE id = ?', (item['job_id'],)).fetchone()[0]
        if result:
            updated = json.dumps(_replace(json.loads(result), str(source), str(target)), ensure_ascii=False)
            jobs.update(conn, item['job_id'], result=updated)
    return _item(conn, item['id'])


def rename(conn: sqlite3.Connection, item_id: int, name: str) -> dict:
    """Renombra el archivo en su carpeta; sin extensión, conserva la suya. ValueError si no es solo un nombre."""
    item = _item(conn, item_id)
    clean = name.strip()
    if not clean or clean in ('.', '..') or '/' in clean or '\\' in clean:
        raise ValueError('invalid name')
    source = Path(item['path'])
    target = source.with_name(clean if Path(clean).suffix else clean + source.suffix)
    return _relocate(conn, item, target)


def move(conn: sqlite3.Connection, item_id: int, folder: Path) -> dict:
    """Mueve el archivo a otra carpeta con el mismo nombre. ValueError si la carpeta no existe."""
    item = _item(conn, item_id)
    if not folder.is_dir():
        raise ValueError('not a folder')
    return _relocate(conn, item, folder / Path(item['path']).name)


def delete(conn: sqlite3.Connection, item_id: int, files: bool, whole_job: bool = False, ignore: bool = False) -> int:
    """Borra el registro; con `files`, el archivo (o la carpeta del trabajo) va a la papelera. Devuelve cuántos quitó.

    Sin `files` y con `ignore`, la ruta queda en `library.ignored` para que el escaneo no la vuelva a agregar.
    """
    item = _item(conn, item_id)
    folder = None
    job = jobs.get(conn, item['job_id']) if whole_job and item['job_id'] else None
    if job is not None:
        folder = job['output_dir']
    if files:
        target = Path(folder) if folder else Path(item['path'])
        check_unprotected(target)
        if target.exists():
            send_to_trash(target)
    if not files and ignore:
        stored = settings.get(conn, scan.IGNORED, [])
        ignored = list(stored) if isinstance(stored, list) else []
        settings.set_value(conn, scan.IGNORED, [*ignored, item['path']])
    if folder:
        return conn.execute('DELETE FROM library_items WHERE job_id = ?', (item['job_id'],)).rowcount
    return conn.execute('DELETE FROM library_items WHERE id = ?', (item_id,)).rowcount
