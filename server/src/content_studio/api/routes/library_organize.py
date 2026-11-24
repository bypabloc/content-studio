"""Rutas de etiquetas y proyectos de la biblioteca (spec 020, D-3). Un proyecto agrupa ítems; no copia archivos."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.library import projects, tags

router = APIRouter()
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


class NameIn(BaseModel):
    """Nombre de una etiqueta o de un proyecto."""

    name: str


class ItemsIn(BaseModel):
    """Ítems que se agregan a un proyecto."""

    items: list[int]


def _project(conn: sqlite3.Connection, project_id: int) -> dict:
    try:
        return projects.get(conn, project_id)
    except LookupError as error:
        raise ApiError(404, 'project_not_found', project_id=project_id) from error


@router.post('/library/{item_id}/tags')
def tag_item(item_id: int, body: NameIn, conn: Conn) -> list[str]:
    """Etiqueta el ítem y devuelve sus etiquetas. 422 `invalid_name` si está vacía; 404 si el ítem no existe."""
    try:
        return tags.add(conn, item_id, body.name)
    except ValueError as error:
        raise ApiError(422, 'invalid_name') from error
    except LookupError as error:
        raise ApiError(404, 'item_not_found', item_id=item_id) from error


@router.delete('/library/{item_id}/tags')
def untag_item(item_id: int, name: str, conn: Conn) -> list[str]:
    """Quita la etiqueta `?name=` y devuelve las que quedan (un DELETE no lleva cuerpo)."""
    try:
        return tags.remove(conn, item_id, name)
    except LookupError as error:
        raise ApiError(404, 'item_not_found', item_id=item_id) from error


@router.get('/tags')
def list_tags(conn: Conn) -> list[dict]:
    """Etiquetas en uso con su cantidad de ítems."""
    return tags.list_tags(conn)


@router.get('/projects')
def list_projects(conn: Conn) -> list[dict]:
    """Proyectos con su cantidad de ítems, del más nuevo al más antiguo."""
    return projects.list_projects(conn)


@router.post('/projects', status_code=201)
def create_project(body: NameIn, conn: Conn) -> dict:
    """Crea un proyecto. 422 `invalid_name` si el nombre está vacío."""
    try:
        return projects.create(conn, body.name)
    except ValueError as error:
        raise ApiError(422, 'invalid_name') from error


@router.patch('/projects/{project_id}')
def rename_project(project_id: int, body: NameIn, conn: Conn) -> dict:
    """Renombra el proyecto."""
    _project(conn, project_id)
    try:
        return projects.rename(conn, project_id, body.name)
    except ValueError as error:
        raise ApiError(422, 'invalid_name') from error


@router.delete('/projects/{project_id}', status_code=204)
def delete_project(project_id: int, conn: Conn) -> Response:
    """Borra la agrupación; los archivos y los ítems quedan."""
    if not projects.delete(conn, project_id):
        raise ApiError(404, 'project_not_found', project_id=project_id)
    return Response(status_code=204)


@router.post('/projects/{project_id}/items', status_code=204)
def add_items(project_id: int, body: ItemsIn, conn: Conn) -> Response:
    """Agrega ítems al proyecto. 404 si el proyecto o un ítem no existe."""
    _project(conn, project_id)
    try:
        projects.add_items(conn, project_id, body.items)
    except LookupError as error:
        raise ApiError(404, 'item_not_found', item_id=error.args[0]) from error
    return Response(status_code=204)


@router.delete('/projects/{project_id}/items/{item_id}', status_code=204)
def remove_item(project_id: int, item_id: int, conn: Conn) -> Response:
    """Quita el ítem del proyecto."""
    _project(conn, project_id)
    projects.remove_item(conn, project_id, item_id)
    return Response(status_code=204)
