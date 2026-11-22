"""Rutas del editor (spec 017, D-3): proyectos en `outputs_dir()/editor`, guardado con `If-Match` y recientes.

Un proyecto solo se abre o se guarda dentro de esa carpeta (403 si no). `missing` lista las fuentes que faltan (AC-10).
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.db import settings
from content_studio.editor import store

router = APIRouter(prefix='/editor')
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
