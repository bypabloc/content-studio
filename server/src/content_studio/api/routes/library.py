"""Rutas de la biblioteca (spec 020): carpetas vigiladas, escaneo por la cola y miniaturas.

La miniatura va en `media_router` porque la pide un <img>, que no manda headers: acepta `?token=`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.schemas import Job
from content_studio.db import jobs as job_store
from content_studio.jobs import queue
from content_studio.library import query, scan, storage, thumbs
from content_studio.services import library_scan

router = APIRouter()
media_router = APIRouter()
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


class FolderIn(BaseModel):
    """Carpeta a vigilar: su ruta y un nombre visible opcional."""

    path: str
    name: str | None = None


class ScanIn(BaseModel):
    """Escaneo de una carpeta (o de todas, sin `folder_id`)."""

    folder_id: int | None = None


def item_or_404(conn: sqlite3.Connection, item_id: int) -> dict:
    """El ítem del índice, o 404 `item_not_found`."""
    row = conn.execute('SELECT * FROM library_items WHERE id = ?', (item_id,)).fetchone()
    if row is None:
        raise ApiError(404, 'item_not_found', item_id=item_id)
    return dict(row)


@router.get('/library')
def search(
    conn: Conn,
    q: str | None = None,
    content: bool = False,
    kind: str | None = None,
    media_type: str | None = None,
    tag: str | None = None,
    project: int | None = None,
    folder: int | None = None,
    origin: str | None = None,
    starred: bool | None = None,
    date_from: Annotated[str | None, Query(alias='from')] = None,
    date_to: Annotated[str | None, Query(alias='to')] = None,
    min_dur: float | None = None,
    max_dur: float | None = None,
    sort: str = 'date',
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = query.PAGE_SIZE,
) -> dict:
    """Ítems de la biblioteca con sus filtros; `content` busca también en guiones y transcripciones en disco."""
    try:
        return query.search(
            conn, q=q, content=content, kind=kind, media_type=media_type, tag=tag, project=project, folder=folder,
            origin=origin, starred=starred, date_from=date_from, date_to=date_to, min_dur=min_dur, max_dur=max_dur,
            sort=sort, page=page, page_size=page_size,
        )  # fmt: skip
    except ValueError as error:
        raise ApiError(422, 'invalid_library_query') from error


@router.get('/library/storage')
def storage_summary(request: Request, conn: Conn) -> dict:
    """Espacio por tipo, lo más pesado, las tomas no elegidas y los totales en disco (spec 020, D-5)."""
    return storage.summary(conn, paths.outputs_dir(request.app.state.db_path))


@router.get('/library/folders')
def list_folders(conn: Conn) -> list[dict]:
    """Las carpetas vigiladas."""
    return scan.list_folders(conn)


@router.post('/library/folders', status_code=201)
def add_folder(body: FolderIn, conn: Conn) -> dict:
    """Agrega una carpeta a vigilar (la misma ruta, una vez). 422 `invalid_folder` si no es una carpeta."""
    try:
        folder_id = scan.add_folder(conn, Path(body.path), body.name)
    except (ValueError, OSError) as error:
        raise ApiError(422, 'invalid_folder') from error
    return next(folder for folder in scan.list_folders(conn) if folder['id'] == folder_id)


@router.delete('/library/folders/{folder_id}', status_code=204)
def remove_folder(folder_id: int, conn: Conn) -> Response:
    """Deja de vigilarla y quita sus ítems del índice; los archivos quedan en disco."""
    if not scan.remove_folder(conn, folder_id):
        raise ApiError(404, 'folder_not_found', folder_id=folder_id)
    return Response(status_code=204)


@router.post('/library/scan', status_code=201, response_model=Job)
def enqueue_scan(body: ScanIn, request: Request, conn: Conn) -> dict:
    """Encola `library.scan` (CPU): la Biblioteca lo pide al abrir si el último tiene más de 5 min, y «Actualizar»."""
    params = {} if body.folder_id is None else {'folder_id': body.folder_id}
    try:
        job_id = queue.enqueue(conn, library_scan.KIND, params, request.app.state.services)
    except queue.InvalidJob as error:
        raise ApiError(422, 'invalid_folder') from error
    job = job_store.get(conn, job_id)
    assert job is not None  # recién encolado
    return job


@media_router.get('/library/thumb/{item_id}')
def thumbnail(item_id: int, conn: Conn) -> FileResponse:
    """JPEG de la miniatura del video o la imagen. 422 `no_thumbnail` si es audio o no se pudo sacar el cuadro."""
    item = item_or_404(conn, item_id)
    try:
        target = thumbs.thumbnail(item)
    except ValueError as error:
        raise ApiError(422, 'no_thumbnail') from error
    return FileResponse(target, media_type='image/jpeg')
