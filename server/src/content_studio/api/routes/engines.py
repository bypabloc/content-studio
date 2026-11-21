"""Catálogo e instalaciones de motores de la app."""

import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes.jobs import NewJob, create_job
from content_studio.api.schemas import Job
from content_studio.engines import installer, recipes
from content_studio.services import engine_install, engine_uninstall

router = APIRouter()
Db = Annotated[sqlite3.Connection, Depends(get_conn)]


class EngineInfo(BaseModel):
    """Estado, requisitos y metadatos de un motor."""

    engine: str
    family: str
    size_gb: float
    vram_gb: float
    cpu: bool
    license: str
    commercial: bool
    status: str
    owner: str | None
    size_bytes: int
    job_id: int | None
    verification: dict | None


def _recipe(name: str) -> recipes.Recipe:
    try:
        return recipes.load(name)
    except (FileNotFoundError, ValueError) as error:
        raise ApiError(404, 'unknown_engine', model=name) from error


def _storage(request: Request) -> Path:
    return paths.engines_dir(request.app.state.db_path)


@router.get('/engines', response_model=list[EngineInfo])
def engines(request: Request, conn: Db) -> list[dict]:
    """Lista las recetas con la propiedad y el estado actual de cada motor."""
    return installer.list_engines(conn, _storage(request))


@router.post('/engines/{name}/install', status_code=201, response_model=Job)
def install(name: str, request: Request, conn: Db, repair: bool = False) -> dict:
    """Encola una instalación o una reparación de la app."""
    recipe = _recipe(name)
    try:
        installer.check_license(conn, name)
    except installer.InstallError as error:
        raise ApiError(409, 'engine_license_required') from error
    if repair and installer.read_manifest(_storage(request) / name).get('owner') != 'app':
        raise ApiError(409, 'engine_external')
    return create_job(
        NewJob(kind=engine_install.KIND, params={'engine': recipe.engine, 'repair': repair}), request, conn
    )


@router.post('/engines/{name}/uninstall', status_code=201, response_model=Job)
def uninstall(name: str, request: Request, conn: Db, force: bool = False) -> dict:
    """Encola un borrado de archivos administrados por la app."""
    recipe = _recipe(name)
    root = _storage(request)
    if installer.read_manifest(root / name).get('owner') != 'app':
        if installer.engine_venv(recipe, root).is_dir():
            if not force:
                raise ApiError(409, 'engine_external')
        else:
            raise ApiError(409, 'engine_not_installed', model=name)
    return create_job(NewJob(kind=engine_uninstall.KIND, params={'engine': name, 'force': force}), request, conn)
