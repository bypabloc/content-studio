"""Sondeo de las carpetas de entrada (spec 030, D-2): un archivo estable en dos sondeos se toma y se encola."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import traceback
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from typing import Any

from content_studio.db import connection
from content_studio.inbox import inputs, receipts, store
from content_studio.jobs import queue
from content_studio.runtime.idle import IdleClock
from content_studio.services.registry import SERVICES

INTERVAL_SECONDS = 2.0
JOB_SUFFIX = '.job.json'
SKIP_PREFIXES = ('.', '~$')  # ocultos y los temporales de Office
SKIP_SUFFIXES = ('.part', '.tmp')  # copias a medio escribir
HOLD_PREFIX = 'inbox:'


def scan_once(conn: sqlite3.Connection, services: Mapping[str, Any] = SERVICES, clock: IdleClock | None = None) -> None:
    """Un sondeo de todas las carpetas: toma lo estable, lo encola y asienta los trabajos que terminaron."""
    folders = store.list_folders(conn)
    if clock is not None:
        _holds(clock, folders)
    for folder in folders:
        if not folder['paused']:
            _sweep(conn, folder, services)
    receipts.settle(conn)


def run_forever(db: Path, clock: IdleClock, stop: threading.Event, services: Mapping[str, Any] = SERVICES) -> None:
    """El hilo del server: sondea al arrancar (así toma lo que se soltó con el server apagado) y luego cada
    INTERVAL_SECONDS, hasta que `stop` se active."""
    with closing(connection.connect(db)) as conn:
        while True:
            try:
                scan_once(conn, services, clock)
            except Exception:  # una carpeta rota no debe apagar el sondeo de las demás
                traceback.print_exc()
            if stop.wait(INTERVAL_SECONDS):
                return


def _holds(clock: IdleClock, folders: list[dict[str, Any]]) -> None:
    """Retiene el server mientras una carpeta con keep_awake no esté pausada; suelta las de carpetas quitadas."""
    wanted = {f'{HOLD_PREFIX}{folder["id"]}' for folder in folders if folder['keep_awake'] and not folder['paused']}
    for name in wanted - clock.holds:
        clock.hold(name)
    for name in [held for held in clock.holds if held.startswith(HOLD_PREFIX) and held not in wanted]:
        clock.release(name)


def _sweep(conn: sqlite3.Connection, folder: dict[str, Any], services: Mapping[str, Any]) -> None:
    """Mira los archivos de la raíz: una versión nueva queda `pending`; la que sigue igual en otro sondeo, se toma."""
    root = Path(folder['path'])
    for entry in _files(root):
        try:
            stat = entry.stat()
        except OSError:
            continue  # desapareció entre la lista y el stat
        row = store.find_item(conn, folder['id'], entry.name, stat.st_size, stat.st_mtime)
        if row is None:
            store.drop_pending(conn, folder['id'], entry.name)
            store.add_item(conn, folder['id'], entry.name, stat.st_size, stat.st_mtime, 'pending')
        elif row['state'] == 'pending':
            _take(conn, folder, root, row, services)


def _files(root: Path) -> list[os.DirEntry[str]]:
    """Los archivos visibles de la raíz: ni subcarpetas ni temporales."""
    with os.scandir(root) as entries:
        return [entry for entry in entries if entry.is_file() and _visible(entry.name)]


def _visible(name: str) -> bool:
    return not name.startswith(SKIP_PREFIXES) and not name.endswith(SKIP_SUFFIXES)


def _take(
    conn: sqlite3.Connection, folder: dict[str, Any], root: Path, row: dict[str, Any], services: Mapping[str, Any]
) -> None:
    """Mueve el archivo a processing/ y lo encola; si no pasa la validación, queda en failed/ con su error."""
    name = row['name']
    taken = root / 'processing' / name
    try:
        os.replace(root / name, taken)
    except OSError:
        return  # quien lo escribe lo tiene abierto: el próximo sondeo lo intenta de nuevo
    store.update_item(conn, row['id'], state='processing')
    try:
        job_id = _enqueue(conn, folder, taken, services)
    except queue.InvalidJob as error:
        _fail_taken(conn, row, root, error.errors[0]['code'], error.errors)
        return
    except store.InboxError as error:
        _fail_taken(conn, row, root, error.code, [])
        return
    store.update_item(conn, row['id'], job_id=job_id)


def _fail_taken(conn: sqlite3.Connection, row: dict[str, Any], root: Path, code: str, errors: list[dict]) -> None:
    receipts.fail(conn, row['id'], root, row['name'], code=code, message=code, errors=errors)


def _enqueue(conn: sqlite3.Connection, folder: dict[str, Any], taken: Path, services: Mapping[str, Any]) -> int:
    """Encola el archivo con el tipo de la carpeta, o con el tipo y los parámetros de su `.job.json`."""
    if taken.name.endswith(JOB_SUFFIX):
        kind, params = _job_file(taken, Path(folder['path']), services)
    else:
        kind = folder['kind']
        params = {**folder['params'], inputs.INPUT_PARAM[kind]: inputs.input_value(kind, taken.resolve())}
    return queue.enqueue(conn, kind, params, services)


def _job_file(path: Path, root: Path, services: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """El tipo y los parámetros de un `.job.json`; una ruta relativa que existe en la carpeta pasa a absoluta."""
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise store.InboxError('invalid_job_file') from error
    kind = data.get('kind') if isinstance(data, dict) else None
    params = data.get('params') if isinstance(data, dict) else None
    if not isinstance(kind, str) or not isinstance(params, dict):
        raise store.InboxError('invalid_job_file')
    if kind not in services:
        raise store.InboxError('unknown_kind', kind=kind)
    return kind, {key: _absolute(value, root) for key, value in params.items()}


def _absolute(value: object, root: Path) -> object:
    """Una ruta relativa que existe dentro de la carpeta pasa a absoluta; cualquier otro valor queda igual."""
    if isinstance(value, str) and not Path(value).is_absolute() and (root / value).exists():
        return str((root / value).resolve())
    return value
