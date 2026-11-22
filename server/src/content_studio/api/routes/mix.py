"""Rutas de Mezcla (spec 016, D-3): proyectos de `mix_projects`, su `mix.json` en disco y la curva de ducking.

`POST /mix/prepare` crea el proyecto. Su voz sale de la caché de transcripciones o se transcribe en un trabajo
`transcribe`: `GET` completa los tramos cuando ese trabajo termina. El render es el trabajo `mix.render`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.paths_guard import allowed_file
from content_studio.api.routes.jobs import JobId
from content_studio.db import jobs as store
from content_studio.db import mix_projects, settings
from content_studio.jobs import queue
from content_studio.mix import project
from content_studio.transcription import cache, models

router = APIRouter()
PENDING = ('queued', 'running')
VIDEO_MODES = ('replace', 'under')


class PrepareIn(BaseModel):
    """Las pistas del proyecto: la voz, la música y un video opcional con su modo."""

    voice: str
    music: str
    video: str | None = None
    video_mode: str = 'replace'


class EditIn(BaseModel):
    """Las regiones de voz editadas (segundos de la voz, sin intro) y los parámetros que cambian."""

    regions: list[tuple[float, float]]
    params: dict[str, Any] = {}


def _row(conn: sqlite3.Connection, project_id: int) -> dict:
    """El proyecto registrado, o 404."""
    row = mix_projects.get(conn, project_id)
    if row is None:
        raise ApiError(404, 'mix_project_not_found', project_id=project_id)
    return row


def _resolve(conn: sqlite3.Connection, row: dict) -> dict:
    """Si el trabajo de transcripción ya terminó, sus tramos entran al proyecto y su JSON va a la caché."""
    doc_path = Path(row['doc_path'])
    doc = project.load(doc_path)
    job_id = doc['transcribe_job']
    if doc['regions'] or job_id is None:
        return doc
    job = store.get(conn, job_id)
    if job is None or job['status'] != 'done':
        return doc
    words = Path(job['output_dir']) / 'words.json'
    voice = Path(doc['voice'])
    cache.store(conn, *project.transcript_key(voice, job['params']['model']), str(words))
    doc['regions'] = project.speech_regions(words, doc['params'])
    project.save(doc_path, doc)
    mix_projects.touch(conn, row['id'])
    return doc


def _status(conn: sqlite3.Connection, doc: dict) -> str:
    """`ready` con tramos; `transcribing` mientras su trabajo corre; `failed` si ese trabajo no terminó."""
    if doc['regions'] or doc['transcribe_job'] is None:
        return 'ready'
    job = store.get(conn, doc['transcribe_job'])
    if job is not None and job['status'] in PENDING:
        return 'transcribing'
    return 'failed'


def _view(row: dict, doc: dict, status: str) -> dict[str, Any]:
    """Lo que el client ve del proyecto: pistas, regiones, parámetros y el estado de la transcripción."""
    return {
        'id': row['id'],
        'name': row['name'],
        'voice': doc['voice'],
        'music': doc['music'],
        'video': doc['video'],
        'video_mode': doc['video_mode'],
        'regions': doc['regions'],
        'params': doc['params'],
        'transcribe_job': doc['transcribe_job'],
        'status': status,
    }


@router.post('/mix/prepare', status_code=201)
def prepare(body: PrepareIn, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Crea el proyecto de mezcla. 422 si el modo de video no existe; 403 o 404 si una ruta no sirve."""
    if body.video_mode not in VIDEO_MODES:
        raise ApiError(422, 'unknown_video_mode', mode=body.video_mode)
    voice = allowed_file(request, body.voice)
    music = allowed_file(request, body.music)
    video = allowed_file(request, body.video) if body.video else None
    model = settings.get(conn, 'select.whisper.model', models.RECOMMENDED)
    hit = cache.find(conn, *project.transcript_key(voice, model))
    regions: list[list[float]] = []
    job_id = None
    if hit is not None:
        regions = project.speech_regions(Path(hit), project.DEFAULT_PARAMS)
    else:
        try:
            job_id = queue.enqueue(
                conn,
                'transcribe',
                {'input': str(voice), 'model': model, 'language': project.AUTO_LANGUAGE},
                request.app.state.services,
            )
        except queue.InvalidJob as error:
            first = error.errors[0]
            raise ApiError(422, first['code'], extra={'errors': error.errors}, **first['params']) from error
    project_id = project.create(
        conn,
        request.app.state.db_path,
        voice=voice,
        music=music,
        video=video,
        video_mode=body.video_mode,
        regions=regions,
        params={},
        transcribe_job=job_id,
    )
    row = _row(conn, project_id)
    doc = project.load(Path(row['doc_path']))
    return _view(row, doc, _status(conn, doc))


@router.get('/mix/{project_id}')
def get_project(project_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """El proyecto; si su transcripción terminó desde la última vez, aquí quedan sus tramos."""
    row = _row(conn, project_id)
    doc = _resolve(conn, row)
    return _view(row, doc, _status(conn, doc))


@router.put('/mix/{project_id}')
def put_project(project_id: JobId, body: EditIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Guarda las regiones editadas y los parámetros que cambian (los demás quedan). Devuelve el proyecto."""
    row = _row(conn, project_id)
    doc = project.load(Path(row['doc_path']))
    doc['regions'] = [list(region) for region in body.regions]
    doc['params'] = {**doc['params'], **body.params}
    project.save(Path(row['doc_path']), doc)
    mix_projects.touch(conn, project_id)
    return _view(row, doc, _status(conn, doc))


@router.get('/mix/{project_id}/curve')
def get_curve(project_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, Any]:
    """La curva de ducking del proyecto: su duración y los puntos [segundos, dB] que usa la vista previa."""
    row = _row(conn, project_id)
    return project.curve(_resolve(conn, row))
