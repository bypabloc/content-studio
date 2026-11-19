"""Trabajos de la API (spec 004, D-3 y D-5): alta, lista, detalle, cancelar y reintentar, con errores con código."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.db import jobs as store
from content_studio.jobs import queue

router = APIRouter()


class NewJob(BaseModel):
    """Cuerpo de POST /jobs: el tipo de trabajo y sus parámetros, como los pide su servicio."""

    kind: str
    params: dict[str, Any]


def _found(conn: sqlite3.Connection, job_id: int) -> dict:
    """El trabajo, o 404 si no existe."""
    job = store.get(conn, job_id)
    if job is None:
        raise ApiError(404, 'job_not_found', job_id=job_id)
    return job


@router.post('/jobs', status_code=201)
def create_job(body: NewJob, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Encola el trabajo. 422 con `code` y `message` si el tipo no existe o los parámetros no sirven."""
    services = request.app.state.services
    if body.kind not in services:
        raise ApiError(422, 'unknown_kind', kind=body.kind)
    try:
        job_id = queue.enqueue(conn, body.kind, body.params, services)
    except queue.InvalidJob as error:
        first = error.errors[0]
        raise ApiError(422, first['code'], extra={'errors': error.errors}, **first['params']) from error
    return _found(conn, job_id)


@router.get('/jobs')
def list_jobs(
    conn: Annotated[sqlite3.Connection, Depends(get_conn)],
    kind: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """Trabajos filtrados por tipo y/o estado, en orden de la cola."""
    return store.list_jobs(conn, kind=kind, status=status)


@router.get('/jobs/{job_id}')
def get_job(job_id: int, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Un trabajo, o 404 si no existe."""
    return _found(conn, job_id)


@router.post('/jobs/{job_id}/cancel')
def cancel_job(job_id: int, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Cancela un trabajo en espera o en curso; con el worker activo también termina su proceso."""
    worker = request.app.state.worker
    changed = worker.cancel(job_id) if worker else queue.cancel(conn, job_id)
    return {'cancelled': changed}


@router.post('/jobs/{job_id}/retry', status_code=201)
def retry_job(job_id: int, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Crea un trabajo nuevo con los mismos parámetros. 409 si el original todavía no terminó."""
    _found(conn, job_id)
    try:
        new_id = queue.retry(conn, job_id)
    except ValueError as error:
        raise ApiError(409, 'job_pending', job_id=job_id) from error
    return _found(conn, new_id)
