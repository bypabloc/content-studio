"""Órdenes de la cola (spec 004, D-3): encolar, cancelar, reintentar, reordenar, pausar y reanudar.

La base es la verdad: el worker lee estas filas. Estas funciones no corren nada.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Mapping
from typing import Any

from content_studio.db import jobs, settings
from content_studio.db.connection import utc_now
from content_studio.services.registry import SERVICES
from content_studio.services.storage_move import KIND as STORAGE_MOVE

PAUSED = 'queue.paused'


class InvalidJob(ValueError):
    """Los parámetros no pasan la validación del servicio; `errors` trae {code, params} por cada problema."""

    def __init__(self, errors: list[dict]) -> None:
        """Guarda la lista de errores de validación."""
        super().__init__(f'{len(errors)} invalid parameter(s)')
        self.errors = errors


def enqueue(conn: sqlite3.Connection, kind: str, params: dict, services: Mapping[str, Any] = SERVICES) -> int:
    """Valida con el servicio del tipo y encola el trabajo en su recurso (gpu o cpu). Antes de validar, el servicio
    puede completar los parámetros y dar el grupo de tomas (`prepare`)."""
    service = services[kind]
    prepare = getattr(service, 'prepare', None)
    params, group = prepare(conn, params) if prepare else (params, None)
    errors = service.validate(params)
    if errors:
        raise InvalidJob(errors)
    return jobs.insert(conn, kind, service.RESOURCE, params, group_key=group)


def cancel(conn: sqlite3.Connection, job_id: int) -> bool:
    """Marca como cancelado un trabajo en espera o en curso. False si no existe o ya terminó."""
    job = jobs.get(conn, job_id)
    if job is None or job['status'] not in ('queued', 'running'):
        return False
    if job['kind'] == STORAGE_MOVE and job['status'] == 'running':
        return False  # No se interrumpe un cambio de raíz mientras confirma sus archivos y preferencias.
    jobs.update(conn, job_id, status='cancelled', finished_at=utc_now())
    return True


def retry(conn: sqlite3.Connection, job_id: int) -> int:
    """Crea un trabajo nuevo con los mismos parámetros. Solo sirve si el original ya terminó."""
    job = jobs.get(conn, job_id)
    if job is None or job['status'] in ('queued', 'running'):
        raise ValueError(f'job {job_id} is not finished')
    return jobs.insert(conn, job['kind'], job['resource'], job['params'], group_key=job['group_key'])


def claim(conn: sqlite3.Connection, job_id: int) -> bool:
    """Pasa un trabajo `queued` a `running` si nadie lo tomó antes. Solo un actor gana (server o CLI)."""
    cursor = conn.execute(
        "UPDATE jobs SET status = 'running', started_at = ?, owner_pid = ? WHERE id = ? AND status = 'queued' "
        "AND NOT EXISTS (SELECT 1 FROM jobs AS active WHERE active.status = 'running' "
        "AND (active.kind = ? OR jobs.kind = ? OR ((active.kind LIKE 'engine.%' OR jobs.kind LIKE 'engine.%') "
        "AND COALESCE(json_extract(active.params, '$.engine'), json_extract(active.params, '$.model')) = "
        "COALESCE(json_extract(jobs.params, '$.engine'), json_extract(jobs.params, '$.model')))))",
        (utc_now(), os.getpid(), job_id, STORAGE_MOVE, STORAGE_MOVE),
    )
    return cursor.rowcount == 1


def reorder(conn: sqlite3.Connection, ids: list[int]) -> None:
    """Pone los trabajos en el orden dado dentro de los puestos que ya ocupan: el resto de la cola no se mueve."""
    rows = [row for row in (jobs.get(conn, job_id) for job_id in ids) if row is not None]
    slots = sorted(row['position'] for row in rows)
    for row, position in zip(rows, slots, strict=True):
        jobs.update(conn, row['id'], position=position)


def pause(conn: sqlite3.Connection) -> None:
    """El worker deja de tomar trabajos nuevos; los que corren siguen."""
    settings.set_value(conn, PAUSED, True)


def resume(conn: sqlite3.Connection) -> None:
    """El worker vuelve a tomar trabajos."""
    settings.set_value(conn, PAUSED, False)


def paused(conn: sqlite3.Connection) -> bool:
    """True si la cola está pausada."""
    return bool(settings.get(conn, PAUSED, False))


def _alive(pid: int | None) -> bool:
    """Si el proceso dueño del trabajo sigue vivo. Sin dueño (trabajo anterior a la migración): muerto."""
    if not pid:
        return False
    if sys.platform == 'win32':  # os.kill(pid, 0) termina el proceso en Windows: se pregunta al sistema
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
        return bool(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def recover_interrupted(conn: sqlite3.Connection) -> int:
    """Los `running` cuyo proceso ya no existe pasan a `interrupted` (AC-11). Los de un proceso vivo no se tocan."""
    rows = conn.execute("SELECT id, owner_pid FROM jobs WHERE status = 'running'").fetchall()
    dead = [job_id for job_id, owner in rows if not _alive(owner)]
    for job_id in dead:
        conn.execute(
            "UPDATE jobs SET status = 'error', error_code = 'interrupted', finished_at = ? WHERE id = ?",
            (utc_now(), job_id),
        )
    return len(dead)
