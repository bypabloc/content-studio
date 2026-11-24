"""Estado de herramientas y GPU, y alta de instalaciones asistidas."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes.jobs import NewJob, create_job
from content_studio.api.schemas import Job
from content_studio.services import system_install_tool
from content_studio.system import tools

router = APIRouter()


class BinaryInfo(BaseModel):
    """Ruta al ejecutable y versión que informa."""

    path: str
    version: str


class GpuInfo(BaseModel):
    """Información que reporta el driver de la GPU."""

    name: str
    vram_gb: float
    driver: str
    cuda: str | None


class SystemInfo(BaseModel):
    """Herramientas y adaptador disponibles."""

    ffmpeg: BinaryInfo | None
    git: BinaryInfo | None
    gpu: GpuInfo | None
    subtitles_filter: bool


@router.get('/system', response_model=SystemInfo)
def system() -> tools.System:
    """Detecta el estado actual de ffmpeg, git y GPU."""
    return tools.detect()


@router.post('/system/tools/{name}/install', status_code=201, response_model=Job)
def install(name: str, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Encola la instalación o indica cómo instalar a mano."""
    if name not in tools.PACKAGES:
        raise ApiError(422, 'unknown_system_tool')
    if not tools.winget_path():
        raise ApiError(503, 'tool_install_failed', tool=name, instructions=tools.HELP[name])
    return create_job(NewJob(kind=system_install_tool.KIND, params={'name': name}), request, conn)
