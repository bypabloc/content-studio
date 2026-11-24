"""Rutas de acciones de la biblioteca (spec 020, D-4): detalle con origen, repetir, renombrar, mover y papelera.

Van después de `library.router` (carpetas, espacio): `/library/{id}` no debe tapar `/library/folders`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.schemas import Job
from content_studio.db import jobs as job_store
from content_studio.library import actions

router = APIRouter()
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


class RenameIn(BaseModel):
    """Nombre nuevo, sin carpeta; sin extensión conserva la del archivo."""

    name: str


class MoveIn(BaseModel):
    """Carpeta de destino."""

    folder: str


class DeleteIn(BaseModel):
    """`files` manda a la papelera; `whole_job`, la carpeta del trabajo; `ignore`, no volver a indexar."""

    files: bool = False
    whole_job: bool = False
    ignore: bool = False


class TrashIn(BaseModel):
    """Ítems que van a la papelera de una vez (lo más pesado, tomas no elegidas)."""

    items: list[int]


def _run(item_id: int, action):  # noqa: ANN001, ANN202 - envuelve la acción y traduce sus errores
    try:
        return action()
    except LookupError as error:
        raise ApiError(404, 'item_not_found', item_id=item_id) from error
    except actions.ProtectedPath as error:
        raise ApiError(403, 'protected_path') from error
    except FileExistsError as error:
        raise ApiError(409, 'path_exists', path=str(error)) from error


@router.get('/library/{item_id}')
def detail(item_id: int, conn: Conn) -> dict:
    """El ítem con su origen: trabajo, otras salidas y tomas del mismo grupo."""
    return _run(item_id, lambda: actions.origin(conn, item_id))


@router.post('/library/{item_id}/repeat', status_code=201, response_model=Job)
def repeat(item_id: int, conn: Conn) -> dict:
    """Encola un trabajo nuevo con los mismos parámetros. 409 `no_job` si el archivo no salió de un trabajo."""
    try:
        new_id = _run(item_id, lambda: actions.repeat(conn, item_id))
    except ValueError as error:
        raise ApiError(409, 'no_job', item_id=item_id) from error
    job = job_store.get(conn, new_id)
    assert job is not None  # recién encolado
    return job


@router.post('/library/{item_id}/rename')
def rename(item_id: int, body: RenameIn, conn: Conn) -> dict:
    """Renombra en su carpeta. 409 `path_exists` si el destino existe; nunca sobrescribe."""
    try:
        return _run(item_id, lambda: actions.rename(conn, item_id, body.name))
    except ValueError as error:
        raise ApiError(422, 'invalid_name') from error


@router.post('/library/{item_id}/move')
def move(item_id: int, body: MoveIn, conn: Conn) -> dict:
    """Mueve a otra carpeta con el mismo nombre. 409 si ahí ya existe."""
    try:
        return _run(item_id, lambda: actions.move(conn, item_id, Path(body.folder)))
    except ValueError as error:
        raise ApiError(422, 'invalid_folder') from error


@router.post('/library/{item_id}/delete')
def delete(item_id: int, body: DeleteIn, conn: Conn) -> dict:
    """Quita el registro; con `files`, a la papelera de Windows. 403 `protected_path` en referencias y motores."""
    removed = _run(item_id, lambda: actions.delete(conn, item_id, body.files, body.whole_job, body.ignore))
    return {'removed': removed}


@router.post('/library/trash')
def trash(body: TrashIn, conn: Conn) -> dict:
    """Manda varios ítems a la papelera; se detiene en el primero protegido o que no existe."""
    removed = sum(_run(item_id, lambda i=item_id: actions.delete(conn, i, files=True)) for item_id in body.items)
    return {'removed': removed}
