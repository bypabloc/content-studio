"""Rutas de Subtítulos (spec 014, D-1): proyectos de `subtitle_projects` y su `subtitles.json` en disco.

Un proyecto nace al terminar su trabajo `subtitles.create` (`jobs/worker.py`). POST encola uno nuevo.
"""

from __future__ import annotations

import json
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
from content_studio.subtitles import export, fonts, sources
from content_studio.subtitles.document import load, save
from content_studio.transcription import cache

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


class TranscriptIn(BaseModel):
    """El trabajo `transcribe` ya terminado cuya transcripción se convertirá en un proyecto editable."""

    job_id: int


@router.post('/subtitles/from-transcript', status_code=201)
def create_from_transcript(
    body: TranscriptIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict[str, Any]:
    """Crea un proyecto 014 con `words.json` de un trabajo `transcribe` terminado."""
    job = store.get(conn, body.job_id)
    if job is None:
        raise ApiError(404, 'job_not_found', job_id=body.job_id)
    if job['kind'] != 'transcribe' or job['status'] != 'done':
        raise ApiError(409, 'source_not_done')
    output_dir = Path(job['output_dir'] or '')
    words_file = output_dir / 'words.json'
    if not words_file.is_file():
        raise ApiError(409, 'source_not_done')
    try:
        result = json.loads(words_file.read_text(encoding='utf-8'))
        words = [
            {'word': word['word'], 'start': word['start'], 'end': word['end']}
            for segment in result['segments']
            for word in segment.get('words', [])
        ]
        if not words:
            raise ValueError('empty_transcript')
        source = str(job['params']['input'])
        language = str(result.get('language') or 'es')
        document = sources.from_words(words, source_path=source, kind='file', language=language)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ApiError(422, 'empty_transcript') from error
    name = Path(source).stem or f'editor-{body.job_id}'
    folder = paths.outputs_dir() / 'subtitles' / f'editor-{body.job_id}'
    folder.mkdir(parents=True, exist_ok=True)
    doc_path = folder / 'subtitles.json'
    save(document, doc_path)
    if Path(source).is_file():  # Publicar (spec 021) busca la transcripción del archivo en la caché de la 013
        stat = Path(source).stat()
        params = job['params']
        key = (source, stat.st_mtime, stat.st_size, params['model'], params.get('language', 'auto'))
        cache.store(conn, *key, str(words_file))
    project_id = subtitle_projects.insert(conn, name, source, str(doc_path))
    return subtitle_projects.get(conn, project_id) or {}


class ExportIn(BaseModel):
    """El formato de la exportación (`srt`, `vtt` o `ass`) y, si se pide, el idioma de una pista traducida."""

    format: str
    language: str | None = None


@router.post('/subtitles/{project_id}/export')
def export_project(
    project_id: int, body: ExportIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict[str, str]:
    """Escribe el documento como SRT, VTT o ASS en `out/subtitles/` y devuelve la ruta del archivo."""
    if body.format not in export.FORMATS:
        raise ApiError(422, 'unknown_format', format=body.format)
    document = load(_doc_path(conn, project_id))
    suffix = body.format
    if body.language:
        if body.language not in document.get('tracks', {}):
            raise ApiError(404, 'unknown_track', language=body.language)
        document, suffix = export.with_track(document, body.language), f'{body.language}.{body.format}'
    target = paths.outputs_dir() / 'subtitles' / f'{project_id}-{Path(document["source"]["path"]).stem}.{suffix}'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export.render(document, body.format), encoding='utf-8')
    return {'path': str(target)}


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
