"""Rutas de Subtítulos (spec 014, D-1): proyectos de `subtitle_projects` y su `subtitles.json` en disco.

Un proyecto nace al terminar su trabajo `subtitles.create` (`jobs/worker.py`). POST encola uno nuevo.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes.jobs import JobId
from content_studio.api.schemas import Job
from content_studio.db import jobs as store
from content_studio.db import subtitle_projects
from content_studio.jobs import queue
from content_studio.subtitles import fonts
from content_studio.subtitles.document import load, save

router = APIRouter()


class DocumentIn(BaseModel):
    """El documento entero, como lo guarda `subtitles/document.py`: `version` y `cues` son obligatorios."""

    model_config = ConfigDict(extra='allow')

    version: int
    cues: list[dict[str, Any]]


def _project(conn: sqlite3.Connection, project_id: int) -> dict:
    """El proyecto registrado, o 404."""
    project = subtitle_projects.get(conn, project_id)
    if project is None:
        raise ApiError(404, 'subtitle_project_not_found', project_id=project_id)
    return project


def _doc_path(conn: sqlite3.Connection, project_id: int) -> Path:
    """El `subtitles.json` del proyecto; 404 también si el archivo ya no está en disco."""
    doc = Path(_project(conn, project_id)['doc_path'])
    if not doc.exists():
        raise ApiError(404, 'subtitle_project_not_found', project_id=project_id)
    return doc


@router.get('/subtitles')
def list_all(conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> list[dict[str, Any]]:
    """Los proyectos guardados, del más reciente al más antiguo."""
    return subtitle_projects.list_projects(conn)


@router.post('/subtitles', status_code=201, response_model=Job)
def create_project(
    body: dict[str, Any], request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict:
    """Encola un `subtitles.create` con su origen y parámetros. 422 con `code` si no sirven (como POST /jobs)."""
    try:
        job_id = queue.enqueue(conn, 'subtitles.create', body, request.app.state.services)
    except queue.InvalidJob as error:
        first = error.errors[0]
        raise ApiError(422, first['code'], extra={'errors': error.errors}, **first['params']) from error
    created = store.get(conn, job_id)
    if created is None:  # no pasa: el trabajo acaba de encolarse en la misma conexión
        raise ApiError(404, 'job_not_found', job_id=job_id)
    return created


@router.get('/subtitles/fonts')
def list_font_families() -> list[dict[str, Any]]:
    """Las fuentes para los subtítulos: las incluidas (`bundled: true`) y las instaladas en el sistema (AC-8)."""
    return fonts.list_fonts(paths.DATA / 'fonts', fonts.system_font_files())


@router.get('/subtitles/{project_id}')
def get_document(project_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, Any]:
    """El documento de subtítulos del proyecto."""
    return load(_doc_path(conn, project_id))


@router.put('/subtitles/{project_id}')
def put_document(
    project_id: JobId, body: DocumentIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict[str, Any]:
    """Guarda el documento editado (el client lo manda entero, con un debounce) y lo devuelve."""
    doc = _doc_path(conn, project_id)
    document = body.model_dump()
    save(document, doc)
    subtitle_projects.touch(conn, project_id)
    return document


@router.delete('/subtitles/{project_id}', status_code=204)
def delete_project(project_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> None:
    """Quita el registro y mueve la carpeta del proyecto a `subtitles/.trash/`: no borra archivos."""
    folder = Path(_project(conn, project_id)['doc_path']).parent
    if folder.exists():
        trash = folder.parent / '.trash'
        trash.mkdir(exist_ok=True)
        shutil.move(str(folder), str(trash / folder.name))
    subtitle_projects.delete(conn, project_id)
