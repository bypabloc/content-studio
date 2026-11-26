"""Rutas de la red local (spec 032, 02 §2): una lista cerrada, con el token de cada dispositivo.

Solo lo que un dispositivo emparejado puede hacer: emparejarse, leer el catálogo, subir archivos, pedir trabajos y bajar
sus salidas. Una ruta nueva de la API no aparece aquí sin agregarla a `include` y a su test (AC-5).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path as FsPath
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes import catalog, health
from content_studio.api.routes import jobs as local_jobs
from content_studio.api.schemas import Job
from content_studio.db import connection
from content_studio.db import jobs as store
from content_studio.lan import cert, clients
from content_studio.lan.pairing import PairingError
from content_studio.narration import profiles

Conn = Annotated[sqlite3.Connection, Depends(get_conn)]
pair_router = APIRouter()
jobs_router = APIRouter()
files_router = APIRouter()


def device(scope: str) -> Callable[[Request], dict]:
    """Exige el Bearer de un dispositivo vigente con `scope`; el token local no vale aquí (AC-4)."""

    def check(request: Request) -> dict:
        supplied = request.headers.get('authorization', '').removeprefix('Bearer ')
        with closing(connection.connect(request.app.state.db_path)) as conn:
            client = clients.authenticate(conn, supplied)
        if client is None:
            raise ApiError(401, 'unauthorized')
        if scope not in client['scopes']:
            raise ApiError(403, 'scope_not_allowed', scope=scope)
        request.state.client = client
        return client

    return check


class PairIn(BaseModel):
    """Cuerpo de POST /pair: el PIN que muestra la app y un nombre para reconocer el dispositivo."""

    pin: str = Field(max_length=16)
    name: str = Field(min_length=1, max_length=80)


@pair_router.post('/pair')
def pair(body: PairIn, request: Request, conn: Conn) -> dict:
    """Canjea el PIN por el token del dispositivo (que se muestra solo esta vez) y la huella del certificado."""
    try:
        request.app.state.pairing.redeem(body.pin)
    except PairingError as error:
        if error.code == 'pairing_locked':
            raise ApiError(429, 'pairing_locked') from None
        raise ApiError(401, 'pairing_invalid') from None
    client_id, token = clients.create(conn, body.name)
    cert_path = request.app.state.cert_path
    return {'client_id': client_id, 'token': token, 'fingerprint': cert.fingerprint(cert_path) if cert_path else None}


@jobs_router.get('/voices/profiles')
def voice_profiles() -> list[dict]:
    """Los perfiles de voz, para elegir con cuál narrar."""
    return profiles.list_profiles()


def _own(conn: sqlite3.Connection, request: Request, job_id: int) -> dict:
    """El trabajo si es de este dispositivo; uno ajeno da el mismo 404 que uno que no existe (AC-7)."""
    job = store.get(conn, job_id)
    if job is None or job.get('client_id') != request.state.client['id']:
        raise ApiError(404, 'job_not_found', job_id=job_id)
    return job


@jobs_router.get('/jobs', response_model=list[Job])
def list_jobs(request: Request, conn: Conn) -> list[dict]:
    """Solo los trabajos de este dispositivo, en orden de la cola."""
    return [job for job in store.list_jobs(conn) if job.get('client_id') == request.state.client['id']]


@jobs_router.get('/jobs/{job_id}', response_model=Job)
def get_job(job_id: local_jobs.JobId, request: Request, conn: Conn) -> dict:
    """Un trabajo propio."""
    return _own(conn, request, job_id)


@jobs_router.post('/jobs/{job_id}/cancel')
def cancel_job(job_id: local_jobs.JobId, request: Request, conn: Conn) -> dict:
    """Cancela un trabajo propio."""
    _own(conn, request, job_id)
    return local_jobs.cancel_job(job_id, request, conn)


@jobs_router.get('/jobs/{job_id}/outputs')
def job_outputs(job_id: local_jobs.JobId, request: Request, conn: Conn) -> list[str]:
    """Las salidas de un trabajo propio, por ruta: lo que se baja con /files."""
    _own(conn, request, job_id)
    return local_jobs.job_outputs(job_id, conn)


@files_router.get('/files')
def get_file(path: str, request: Request, conn: Conn) -> FileResponse:
    """Una salida de un trabajo propio; cualquier otra ruta, también de otro dispositivo, da 404 (AC-7)."""
    if '\x00' not in path:
        target = FsPath(path).resolve()
        for job in list_jobs(request, conn):
            folder = job['output_dir']
            if folder and target.is_relative_to(FsPath(folder).resolve()) and target.is_file():
                return FileResponse(target)
    raise ApiError(404, 'not_found')


def include(app: FastAPI, lan_url: str | None) -> None:
    """Monta la lista cerrada de 02 §2 en la app de la red local."""
    jobs_only = [Depends(device('jobs'))]
    files_only = [Depends(device('files'))]
    app.include_router(pair_router)
    app.include_router(health.router, dependencies=jobs_only)
    app.include_router(catalog.router, dependencies=jobs_only)
    app.include_router(jobs_router, dependencies=jobs_only)
    app.include_router(files_router, dependencies=files_only)
    app.state.lan_url = lan_url
