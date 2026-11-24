"""Rutas del asistente (spec 021, D-5): estado, idiomas, resultado de una tarea y aplicar lo aceptado en subtítulos.

Las tareas se encolan con `POST /jobs` (`llm.<tarea>`). El LLM solo propone: `result` devuelve la propuesta y nada
cambia hasta que el usuario acepta (en Narración y Música, el client llena sus campos; en Subtítulos, `apply`).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.db import jobs, settings, subtitle_projects
from content_studio.llm import models
from content_studio.llm.tasks import subtitles_correct, subtitles_keywords, subtitles_translate
from content_studio.subtitles import languages
from content_studio.subtitles.document import load, save

router = APIRouter()
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]
APPLY = {
    'llm.subtitles_translate': lambda doc, result, accepted: subtitles_translate.apply(doc, result),
    'llm.subtitles_correct': subtitles_correct.apply,
    'llm.subtitles_keywords': subtitles_keywords.apply,
}


class LlmModel(BaseModel):
    """Un modelo del asistente: tamaño, VRAM, si es el ★ y si está instalado."""

    model: str
    size_gb: float
    vram_gb: float
    recommended: bool
    installed: bool


class LlmStatus(BaseModel):
    """Si el asistente está activo e instalado, el modelo elegido y el que está cargado (y en cuánto se libera)."""

    enabled: bool
    runtime_installed: bool
    selected: str
    models: list[LlmModel]
    loaded: str | None
    release_in: float | None


class Language(BaseModel):
    """Un idioma de traducción, con su nombre en su idioma."""

    code: str
    name: str
    recommended: bool


class ApplyIn(BaseModel):
    """El trabajo cuya propuesta se aplica y los cues aceptados (todos si no se dice)."""

    job_id: int
    accepted: list[int] | None = None


@router.get('/llm/status', response_model=LlmStatus)
def status(request: Request, conn: Conn) -> dict:
    """El estado del asistente para los botones de IA, Ajustes y la cola."""
    root = paths.engines_dir(request.app.state.db_path)
    warm = getattr(request.app.state.worker, 'llm', None)
    loaded = warm.runtime.model if warm is not None and warm.running else None
    return {
        'enabled': settings.get(conn, 'llm.enabled', True) is not False,
        'runtime_installed': models.server_path(root).is_file(),
        'selected': models.selected(conn),
        'models': models.status(root),
        'loaded': loaded,
        'release_in': warm.release_in() if warm is not None and loaded else None,
    }


@router.get('/llm/languages', response_model=list[Language])
def translation_languages() -> list[dict]:
    """Los idiomas a los que se traducen los subtítulos, con ★ en el inglés."""
    return languages.status()


def _result(conn: sqlite3.Connection, job_id: int) -> tuple[dict, dict]:
    job = jobs.get(conn, job_id)
    if job is None or not job['kind'].startswith('llm.'):
        raise ApiError(404, 'job_not_found', job_id=job_id)
    path = Path(job['output_dir'] or '') / 'result.json'
    if not path.is_file():
        raise ApiError(404, 'llm_result_not_found')
    return job, json.loads(path.read_text(encoding='utf-8'))


@router.get('/llm/jobs/{job_id}/result')
def result(job_id: int, conn: Conn) -> dict:
    """La propuesta de una tarea terminada (result.json de su carpeta)."""
    return _result(conn, job_id)[1]


@router.post('/llm/subtitles/{project_id}/apply')
def apply(project_id: int, body: ApplyIn, conn: Conn) -> dict:
    """Aplica lo aceptado de una traducción, una corrección o unas palabras clave, y devuelve el documento."""
    project = subtitle_projects.get(conn, project_id)
    if project is None:
        raise ApiError(404, 'subtitle_project_not_found', project_id=project_id)
    job, proposal = _result(conn, body.job_id)
    if job['kind'] not in APPLY:
        raise ApiError(422, 'llm_not_applicable')
    path = Path(project['doc_path'])
    doc = APPLY[job['kind']](load(path), proposal, body.accepted)
    save(doc, path)
    return doc
