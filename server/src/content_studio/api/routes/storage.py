"""Rutas y trabajos de almacenamiento de la app."""

import os
import shutil
import sqlite3
from pathlib import Path
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
    """Rutas activas y métricas de espacio de motores y salidas."""

    engines: str
    outputs: str
    engines_used_bytes: int
    engines_free_bytes: int
    outputs_used_bytes: int
    outputs_free_bytes: int


class StorageMove(BaseModel):
    """Raíz que se va a mover y su destino."""

    target: str
    to: str


@router.get('/storage', response_model=StoragePaths)
def storage(request: Request) -> StoragePaths:
    """Expone las raíces activas y el espacio de cada una."""
    database = request.app.state.db_path
    engines = paths.engines_dir(database)
    outputs = paths.outputs_dir(database)
    return StoragePaths(
        engines=str(engines),
        outputs=str(outputs),
        engines_used_bytes=_directory_bytes(engines),
        engines_free_bytes=_free_bytes(engines),
        outputs_used_bytes=_directory_bytes(outputs),
        outputs_free_bytes=_free_bytes(outputs),
    )


def _directory_bytes(root: Path) -> int:
    """Suma archivos regulares sin recorrer enlaces ni rutas que apunten fuera de la raíz."""
    if root.is_symlink() or not root.is_dir():
        return 0
    total = 0
    for current, directories, files in os.walk(root, followlinks=False):
        base = Path(current)
        directories[:] = [name for name in directories if not (base / name).is_symlink()]
        for name in files:
            file = base / name
            if file.is_symlink():
                continue
            try:
                total += file.stat().st_size
            except OSError:
                continue
    return total


def _free_bytes(path: Path) -> int:
    """Consulta el disco de la ruta existente más cercana sin crear la carpeta solicitada."""
    current = path
    while current.is_symlink() or not current.exists():
        if current.parent == current:
            return 0
        current = current.parent
    try:
        return shutil.disk_usage(current).free
    except OSError:
        return 0


@router.post('/storage/move', status_code=201, response_model=Job)
def move(body: StorageMove, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Encola un traslado sin modificar las preferencias por adelantado."""
    return create_job(NewJob(kind=KIND, params=body.model_dump()), request, conn)
