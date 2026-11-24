"""Rutas del editor (spec 017, D-3): proyectos en `outputs_dir()/editor`, guardado con `If-Match` y recientes.

Un proyecto solo se abre o se guarda dentro de esa carpeta (403 si no). `missing` lista las fuentes que faltan (AC-10).
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import sqlite3
import subprocess
from datetime import date
from pathlib import Path
from secrets import token_hex
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.db import settings
from content_studio.editor import effects, store, subtitle_projects

router = APIRouter(prefix='/editor')
preview_router = APIRouter(prefix='/editor')
RECENT = 'editor.recent'
RECENT_MAX = 20


class CreateIn(BaseModel):
    """El nombre del proyecto nuevo."""

    name: str


def _root() -> Path:
    """La carpeta de los proyectos del editor."""
    return paths.outputs_dir() / 'editor'


def _project_file(path: str) -> Path:
    """El `project.json` pedido: 403 si está fuera de la carpeta del editor, 404 si no existe."""
    file = Path(path).resolve()
    if file.name != store.FILE or not file.is_relative_to(_root().resolve()):
        raise ApiError(403, 'forbidden_path')
    if not file.is_file():
        raise ApiError(404, 'editor_project_not_found', path=path)
    return file


def _recent(conn: sqlite3.Connection) -> list[str]:
    """Las rutas de los proyectos recientes, la última abierta primero."""
    return cast(list[str], settings.get(conn, RECENT, []))


def _remember(conn: sqlite3.Connection, file: Path) -> None:
    """Pone el proyecto al frente de los recientes, sin repetirlo y con un máximo de `RECENT_MAX`."""
    others = [p for p in _recent(conn) if p != str(file)]
    settings.set_value(conn, RECENT, [str(file), *others][:RECENT_MAX])


@router.post('/projects', status_code=201)
def create_project(body: CreateIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, Any]:
    """Crea el proyecto en `outputs_dir()/editor/<AAAA-MM-DD>-<slug>/` y devuelve su ruta, su hash y su documento."""
    file = store.create(_root(), body.name, date.today())
    _remember(conn, file)
    doc, digest = store.read(file)
    return {'path': str(file), 'hash': digest, 'doc': doc}


@router.get('/projects/recent')
def recent_projects(conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, list[str]]:
    """Los proyectos abiertos o creados hace poco, la última primero."""
    return {'paths': _recent(conn)}


@router.get('/projects')
def open_project(path: str, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, Any]:
    """El documento, su hash (el `If-Match` del siguiente guardado) y las fuentes que faltan."""
    file = _project_file(path)
    doc, digest = store.read(file)
    _remember(conn, file)
    return {'path': str(file), 'hash': digest, 'doc': doc, 'missing': store.missing(file.parent, doc)}


@router.put('/projects')
def save_project(
    path: str,
    body: dict[str, Any],
    if_match: Annotated[str, Header()],
) -> dict[str, Any]:
    """Guarda el documento si el archivo sigue con el hash `If-Match`; si no, 409 `project_changed` y no escribe."""
    file = _project_file(path)
    try:
        digest = store.write(file, body, if_match)
    except store.ProjectChanged as error:
        raise ApiError(409, 'project_changed') from error
    return {'hash': digest, 'missing': store.missing(file.parent, body)}


@router.get('/projects/frame')
def project_frame(
    path: str,
    conn: Annotated[sqlite3.Connection, Depends(get_conn)],
    t: float = Query(0, ge=0),
) -> FileResponse:
    """Devuelve como PNG el fotograma exacto del lienzo en `t`, con caché por revisión del proyecto."""
    file = _project_file(path)
    doc, digest = store.read(file)
    if not _finite_time(t):
        raise ApiError(422, 'unreadable_media')
    try:
        subtitle_documents = subtitle_projects.load_documents(doc, conn) if conn is not None else {}
    except subtitle_projects.MissingSubtitleProject as error:
        raise ApiError(404, 'subtitle_project_not_found', project_id=error.project_id) from error
    key = _frame_cache_key(file, doc, digest, t, subtitle_documents)
    frame = paths.outputs_dir() / 'tmp' / 'editor-frames' / f'{key}.png'
    if not frame.is_file() or not frame.stat().st_size:
        frame.parent.mkdir(parents=True, exist_ok=True)
        temporary = frame.with_name(f'{frame.stem}.{token_hex(6)}.png')
        try:
            from content_studio.editor import render_video

            render_video.render_frame(doc, file.parent, t, temporary, subtitle_documents=subtitle_documents)
            if not temporary.is_file() or not temporary.stat().st_size:
                raise ValueError('unreadable_media')
            os.replace(temporary, frame)
        except (OSError, ValueError, render_video.render_audio.RenderError, subprocess.CalledProcessError) as error:
            if isinstance(error, render_video.render_audio.RenderError):
                raise ApiError(422, error.code, **error.params) from error
            raise ApiError(422, 'unreadable_media') from error
        finally:
            temporary.unlink(missing_ok=True)
    return FileResponse(frame, media_type='image/png')


@preview_router.get('/projects/media')
def project_media(path: str, source: str) -> FileResponse:
    """Sirve una fuente visual del proyecto; los videos usan su proxy y la ruta acepta token de consulta."""
    file = _project_file(path)
    doc, _ = store.read(file)
    clip = next(
        (
            item
            for item in doc.get('clips', [])
            if item.get('media') in {'video', 'image', 'text'} and item.get('src') == source
        ),
        None,
    )
    if clip is None:
        raise ApiError(404, 'fs_media_not_found', path=source)
    original = Path(source)
    original = (original if original.is_absolute() else file.parent / original).resolve()
    if not original.is_file():
        raise ApiError(404, 'fs_media_not_found', path=source)
    if clip['media'] == 'image':
        from content_studio.media.formats import IMAGE_EXTENSIONS

        if original.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ApiError(422, 'unreadable_media')
        target = original
    elif clip['media'] == 'text':
        media_root = (file.parent / 'media').resolve()
        if source != clip.get('raster') or Path(source).is_absolute() or not original.is_relative_to(media_root):
            raise ApiError(404, 'fs_media_not_found', path=source)
        target = original
    else:
        from content_studio.editor import proxy

        try:
            target = proxy.create(original, file.parent)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            raise ApiError(422, 'unreadable_media') from error
    media_type = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
    return FileResponse(target, media_type=media_type)


@preview_router.get('/projects/luts')
def project_lut(path: str, source: str) -> FileResponse:
    """Sirve una LUT 3D declarada por un clip y dentro de los medios del proyecto."""
    file = _project_file(path)
    doc, _ = store.read(file)
    if not any(
        isinstance(clip.get('color'), dict) and clip['color'].get('lut') == source for clip in doc.get('clips', [])
    ):
        raise ApiError(404, 'fs_media_not_found', path=source)
    try:
        target = effects.resolve_lut(file.parent, source)
    except ValueError as error:
        raise ApiError(404, 'fs_media_not_found', path=source) from error
    if not target.is_file():
        raise ApiError(404, 'fs_media_not_found', path=source)
    return FileResponse(
        target,
        media_type='text/plain; charset=utf-8',  # i18n-ignore: tipo MIME de un LUT, no es texto de interfaz
    )


def _finite_time(value: float) -> bool:
    """El fotograma no acepta `NaN` ni infinitos."""
    return value == value and value not in (float('inf'), float('-inf'))


def _frame_cache_key(
    file: Path,
    doc: dict[str, Any],
    digest: str,
    time: float,
    subtitle_documents: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Incluye en la caché la revisión del proyecto y el estado de cada fuente visual."""
    stat = file.stat()
    sources: list[tuple[str, int | None, int | None]] = []
    for clip in doc.get('clips', []):
        if clip.get('media') not in {'video', 'image', 'text'}:
            continue
        source = Path(clip['src'])
        source = (source if source.is_absolute() else file.parent / source).resolve()
        try:
            media_stat = source.stat()
            sources.append((str(source), media_stat.st_mtime_ns, media_stat.st_size))
        except OSError:
            sources.append((str(source), None, None))
        color = clip.get('color')
        lut = color.get('lut') if isinstance(color, dict) else None
        if lut:
            try:
                source = effects.resolve_lut(file.parent, lut)
                stat = source.stat()
                sources.append((str(source), stat.st_mtime_ns, stat.st_size))
            except (OSError, ValueError):
                sources.append((lut, None, None))
    subtitle_hash = hashlib.sha256(repr(sorted((subtitle_documents or {}).items())).encode('utf-8')).hexdigest()
    identity = (str(file.resolve()), stat.st_mtime_ns, stat.st_size, digest, time, tuple(sources), subtitle_hash)
    return hashlib.sha256(repr(identity).encode('utf-8')).hexdigest()


@router.post('/projects/media', status_code=201)
async def upload_recording(path: str, request: Request) -> dict[str, str | float]:
    """Guarda una toma WAV o una imagen PNG dentro de la carpeta de medios del proyecto."""
    file = _project_file(path)
    content_type = request.headers.get('content-type', '').split(';', maxsplit=1)[0].strip().lower()
    if content_type == 'image/png':
        clip_id = request.query_params.get('clip_id', '')
        digest = request.query_params.get('sha256', '')
        try:
            src = store.save_text_raster(file.parent, await request.body(), clip_id, digest)
        except ValueError as error:
            raise ApiError(422, 'editor_text_raster_invalid') from error
        return {'src': src}
    if content_type != 'audio/wav':
        raise ApiError(422, 'editor_recording_invalid')
    try:
        src, duration = store.save_recording(file.parent, await request.body())
    except ValueError as error:
        raise ApiError(422, 'editor_recording_invalid') from error
    return {'src': src, 'duration': duration}


@router.post('/projects/luts', status_code=201)
async def upload_lut(path: str, request: Request) -> dict[str, str]:
    """Valida una LUT 3D `.cube` y la guarda dentro de los medios del proyecto."""
    file = _project_file(path)
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > effects.LUT_LIMIT:
            raise ApiError(422, 'editor_lut_invalid')
        data.extend(chunk)
    try:
        src = effects.save_lut(file.parent, bytes(data))
    except ValueError as error:
        raise ApiError(422, 'editor_lut_invalid') from error
    return {'src': src}
