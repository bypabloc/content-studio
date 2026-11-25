"""Carpetas de entrada de la API (spec 030, 02 §2): alta con validación, lista, pausa y baja, con errores con código."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.inbox import store
from content_studio.jobs import queue

router = APIRouter(prefix='/inbox')


class NewFolder(BaseModel):
    """Cuerpo de POST /inbox/folders: la carpeta, el tipo de trabajo que hace con cada archivo y sus parámetros."""

    path: str
    kind: str
    params: dict[str, Any] = {}
    keep_awake: bool = True


class PauseIn(BaseModel):
    """Cuerpo de POST /inbox/folders/{id}/pause: true pausa la carpeta y false la reanuda."""

    paused: bool = True


class InboxFolder(BaseModel):
    """Una carpeta de entrada tal como la devuelve la API."""

    id: int
    path: str
    kind: str
    params: dict[str, Any]
    keep_awake: bool
    paused: bool
    created_at: str


def _found(conn: sqlite3.Connection, folder_id: int) -> dict[str, Any]:
    """La carpeta, o 404 si no está registrada."""
    folder = store.get(conn, folder_id)
    if folder is None:
        raise ApiError(404, 'inbox_folder_not_found', folder_id=folder_id)
    return folder


@router.post('/folders', status_code=201, response_model=InboxFolder)
def create_folder(body: NewFolder, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Registra la carpeta. 422 con `code` si la ruta, el tipo o los parámetros no sirven."""
    try:
        folder_id = store.register(conn, body.path, body.kind, body.params, body.keep_awake, request.app.state.services)
    except store.InboxError as error:
        raise ApiError(422, error.code, **error.params) from error
    except queue.InvalidJob as error:
        first = error.errors[0]
        raise ApiError(422, first['code'], extra={'errors': error.errors}, **first['params']) from error
    return _found(conn, folder_id)


@router.get('/folders', response_model=list[InboxFolder])
def list_folders(conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> list[dict]:
    """Las carpetas registradas, en orden de alta."""
    return store.list_folders(conn)


@router.post('/folders/{folder_id}/pause', response_model=InboxFolder)
def pause_folder(folder_id: int, conn: Annotated[sqlite3.Connection, Depends(get_conn)], body: PauseIn) -> dict:
    """Pausa la carpeta (o la reanuda con paused en false): mientras está pausada no toma archivos."""
    _found(conn, folder_id)
    store.set_paused(conn, folder_id, body.paused)
    return _found(conn, folder_id)


@router.delete('/folders/{folder_id}', status_code=204)
def remove_folder(folder_id: int, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> Response:
    """Quita la carpeta del registro; sus archivos no se tocan. 404 si no existe."""
    if not store.remove(conn, folder_id):
        raise ApiError(404, 'inbox_folder_not_found', folder_id=folder_id)
    return Response(status_code=204)
