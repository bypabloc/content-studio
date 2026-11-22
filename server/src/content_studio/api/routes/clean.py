"""Rutas del limpiador (spec 013, D-4 y AC-7): ver los cortes de un análisis, replanificarlos sin GPU, guardarlos y
encolar el render. Los trabajos se encolan con `POST /jobs` (`clean.analyze`); aquí están sus cortes."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes.jobs import JobId
from content_studio.api.schemas import Job
from content_studio.clean import cuts as cut_file
from content_studio.clean.cuts import replan
from content_studio.clean.plan import Span
from content_studio.db import jobs as store
from content_studio.jobs import queue

router = APIRouter()


class PlanIn(BaseModel):
    """Parámetros para replanificar: hueco mínimo, margen y bordes."""

    min_gap: float = 0.5
    padding: float = 0.15
    edges: bool = True


class CutsIn(BaseModel):
    """Los cortes que el usuario dejó: se guardan tal cual en cuts.json."""

    cuts: list[dict[str, Any]]


def _analysis(conn: sqlite3.Connection, job_id: int) -> tuple[dict, dict, Path]:
    """El trabajo, el documento de cortes de un análisis terminado y su carpeta. 404 si no existe; 409 si no es un
    análisis del limpiador o no terminó."""
    job = store.get(conn, job_id)
    if job is None:
        raise ApiError(404, 'job_not_found', job_id=job_id)
    if job['kind'] != 'clean.analyze':
        raise ApiError(409, 'job_not_clean', job_id=job_id)
    if job['status'] != 'done':
        raise ApiError(409, 'job_not_done', job_id=job_id)
    folder = Path(job['output_dir'])
    return job, cut_file.load(folder), folder


def _words(document: dict) -> list[Span]:
    transcript = json.loads(Path(document['transcript']).read_text(encoding='utf-8'))
    return [word for segment in transcript['segments'] for word in segment['words']]


@router.get('/clean/{job_id}')
def get_cuts(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """El documento de cortes del análisis: parámetros, duración, idioma y cortes."""
    _, document, _ = _analysis(conn, job_id)
    return document


@router.post('/clean/{job_id}/plan')
def plan_cuts(job_id: JobId, body: PlanIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Replanifica con otro hueco o margen, sin GPU: los cortes sin editar cambian y los editados se conservan.
    No guarda nada; para guardar, `PUT /clean/{job_id}/cuts`."""
    _, document, _ = _analysis(conn, job_id)
    found = replan(
        _words(document),
        document['duration'],
        min_gap=body.min_gap,
        padding=body.padding,
        edges=body.edges,
        previous=document['cuts'],
    )
    return {**document, 'params': body.model_dump(), 'cuts': found}


@router.put('/clean/{job_id}/cuts')
def save_cuts(job_id: JobId, body: CutsIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Guarda los cortes del usuario en cuts.json. 422 si un corte no tiene inicio menor que su fin dentro de la
    duración."""
    _, document, folder = _analysis(conn, job_id)
    for cut in body.cuts:
        if not 0 <= cut['start'] < cut['end'] <= document['duration']:
            raise ApiError(422, 'invalid_cut')
    document['cuts'] = [{'enabled': True, **cut} for cut in body.cuts]
    cut_file.save(folder, document)
    return document


@router.post('/clean/{job_id}/render', status_code=201, response_model=Job)
def render(job_id: JobId, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Encola `clean.render` con el original del análisis y su carpeta de cortes."""
    job, _, folder = _analysis(conn, job_id)
    original = job['params']['input']
    try:
        new_id = queue.enqueue(
            conn, 'clean.render', {'input': original, 'analysis': str(folder)}, request.app.state.services
        )
    except queue.InvalidJob as error:
        first = error.errors[0]
        raise ApiError(422, first['code'], extra={'errors': error.errors}, **first['params']) from error
    created = store.get(conn, new_id)
    if created is None:  # no pasa: acaba de encolarse en la misma conexión
        raise ApiError(500, 'job_not_found', job_id=new_id)
    return created
