"""Rutas y trabajos de almacenamiento de la app."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.routes.jobs import NewJob, create_job
from content_studio.api.schemas import Job
from content_studio.services.storage_move import KIND

router = APIRouter()


class StoragePaths(BaseModel):
    """Raíces activas de motores y salidas."""

    engines: str
    outputs: str


class StorageMove(BaseModel):
    """Raíz que se va a mover y su destino."""

    target: str
    to: str


@router.get('/storage', response_model=StoragePaths)
def storage(request: Request) -> StoragePaths:
    """Expone las raíces activas."""
    database = request.app.state.db_path
    return StoragePaths(engines=str(paths.engines_dir(database)), outputs=str(paths.outputs_dir(database)))


@router.post('/storage/move', status_code=201, response_model=Job)
def move(body: StorageMove, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Encola un traslado sin modificar las preferencias por adelantado."""
    return create_job(NewJob(kind=KIND, params=body.model_dump()), request, conn)
