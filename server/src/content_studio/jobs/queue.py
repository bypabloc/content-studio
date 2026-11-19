"""Órdenes de la cola (spec 004, D-3): encolar, cancelar, reintentar, reordenar, pausar y reanudar.

La base es la verdad: el worker lee estas filas. Estas funciones no corren nada.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from typing import Any

from content_studio.db import jobs, settings
from content_studio.db.connection import utc_now
from content_studio.services.registry import SERVICES

PAUSED = 'queue.paused'


class InvalidJob(ValueError):
    """Los parámetros no pasan la validación del servicio; `errors` trae {code, params} por cada problema."""

    def __init__(self, errors: list[dict]) -> None:
        """Guarda la lista de errores de validación."""
        super().__init__(f'{len(errors)} invalid parameter(s)')
        self.errors = errors


def enqueue(conn: sqlite3.Connection, kind: str, params: dict, services: Mapping[str, Any] = SERVICES) -> int:
    """Valida con el servicio del tipo y encola el trabajo en su recurso (gpu o cpu)."""
    service = services[kind]
    errors = service.validate(params)
    if errors:
        raise InvalidJob(errors)
    return jobs.insert(conn, kind, service.RESOURCE, params)


def cancel(conn: sqlite3.Connection, job_id: int) -> bool:
    """Marca como cancelado un trabajo en espera o en curso. False si no existe o ya terminó."""
    job = jobs.get(conn, job_id)
    if job is None or job['status'] not in ('queued', 'running'):
        return False
    jobs.update(conn, job_id, status='cancelled', finished_at=utc_now())
    return True


def retry(conn: sqlite3.Connection, job_id: int) -> int:
    """Crea un trabajo nuevo con los mismos parámetros. Solo sirve si el original ya terminó."""
    job = jobs.get(conn, job_id)
    if job is None or job['status'] in ('queued', 'running'):
        raise ValueError(f'job {job_id} is not finished')
    return jobs.insert(conn, job['kind'], job['resource'], job['params'])


def reorder(conn: sqlite3.Connection, ids: list[int]) -> None:
    """Pone los trabajos en el orden dado: el primero de la lista sale primero."""
    for position, job_id in enumerate(ids, 1):
        jobs.update(conn, job_id, position=position)


def pause(conn: sqlite3.Connection) -> None:
    """El worker deja de tomar trabajos nuevos; los que corren siguen."""
    settings.set_value(conn, PAUSED, True)


def resume(conn: sqlite3.Connection) -> None:
    """El worker vuelve a tomar trabajos."""
    settings.set_value(conn, PAUSED, False)


def paused(conn: sqlite3.Connection) -> bool:
    """True si la cola está pausada."""
    return bool(settings.get(conn, PAUSED, False))


def recover_interrupted(conn: sqlite3.Connection) -> int:
    """Los `running` que quedaron de una caída pasan a error `interrupted` (AC-11). Devuelve cuántos."""
    cursor = conn.execute(
        "UPDATE jobs SET status = 'error', error_code = 'interrupted', finished_at = ? WHERE status = 'running'",
        (utc_now(),),
    )
    return cursor.rowcount
