"""Trabajos de la API (spec 004, D-3 y D-5): alta, lista, detalle, cancelar y reintentar, con errores con código."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path as FsPath
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.schemas import ChooseIn, Job
from content_studio.db import jobs as store
from content_studio.jobs import queue
from content_studio.music.manifest import MANIFEST

router = APIRouter()
JobId = Annotated[int, Path(ge=1, le=2**63 - 1)]  # los ids de SQLite van de 1 a 2^63-1: fuera, 422 y no 500
TAKE_KINDS = ('narration', 'narration.regenerate')  # las tomas que se pueden elegir con ★


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


@router.post('/jobs', status_code=201, response_model=Job)
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


@router.get('/jobs', response_model=list[Job])
def list_jobs(
    conn: Annotated[sqlite3.Connection, Depends(get_conn)],
    kind: str | None = None,
    status: str | None = None,
    group_key: str | None = None,
) -> list[dict]:
    """Trabajos filtrados por tipo, estado y/o grupo de tomas, en orden de la cola."""
    return store.list_jobs(conn, kind=kind, status=status, group_key=group_key)


@router.get('/jobs/{job_id}', response_model=Job)
def get_job(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Un trabajo, o 404 si no existe."""
    return _found(conn, job_id)


OUTPUT_SUFFIXES = ('.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.mp4', '.mov', '.mkv', '.webm')


@router.get('/jobs/{job_id}/outputs')
def job_outputs(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> list[str]:
    """Los audios y videos de la carpeta del trabajo, por ruta: lo que «Del historial» de Mezcla puede elegir."""
    folder = FsPath(_found(conn, job_id)['output_dir'] or '')
    if not folder.is_dir():
        return []
    return sorted(str(path) for path in folder.iterdir() if path.suffix.lower() in OUTPUT_SUFFIXES)


@router.post('/jobs/{job_id}/cancel')
def cancel_job(job_id: JobId, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Cancela un trabajo en espera o en curso; con el worker activo también termina su proceso."""
    worker = request.app.state.worker
    changed = worker.cancel(job_id) if worker else queue.cancel(conn, job_id)
    return {'cancelled': changed}


@router.post('/jobs/{job_id}/retry', status_code=201, response_model=Job)
def retry_job(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Crea un trabajo nuevo con los mismos parámetros. 409 si el original todavía no terminó."""
    _found(conn, job_id)
    try:
        new_id = queue.retry(conn, job_id)
    except ValueError as error:
        raise ApiError(409, 'job_pending', job_id=job_id) from error
    return _found(conn, new_id)


@router.post('/jobs/{job_id}/star', response_model=Job)
def star_job(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Marca la toma como la elegida de su grupo y desmarca las demás del grupo. 404 si no existe; 409 si no es una
    toma terminada de narración (una en cola o con error no puede quitarle la marca a la buena)."""
    job = _found(conn, job_id)
    if job['status'] != 'done' or job['kind'] not in TAKE_KINDS:
        raise ApiError(409, 'job_not_a_take', job_id=job_id)
    store.star(conn, job_id)
    return _found(conn, job_id)


@router.post('/jobs/{job_id}/choose')
def choose_track(job_id: JobId, body: ChooseIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Elige una pista de un trabajo de música: queda como `chosen` de su `tracks.json`. 409 si el trabajo no es de
    música o no terminó; 422 si el archivo no es una de sus pistas."""
    job = _found(conn, job_id)
    manifest_path = FsPath(job['output_dir'] or '') / MANIFEST
    if job['status'] != 'done' or job['kind'] != 'music' or not manifest_path.is_file():
        raise ApiError(409, 'job_not_music_tracks', job_id=job_id)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if body.file not in {track['file'] for track in manifest['tracks']}:
        raise ApiError(422, 'unknown_track', file=body.file)
    manifest['chosen'] = body.file
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest
