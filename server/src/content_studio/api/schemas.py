"""Modelos de respuesta de la API (spec 005, D-3): de aquí sale el schema OpenAPI con el que se tipa el client."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class Job(BaseModel):
    """Una fila de la cola: `GET /jobs`, `GET /jobs/{id}`, reintentar y el evento SSE `job`."""

    id: int
    kind: str
    resource: Literal['gpu', 'cpu']
    status: Literal['queued', 'running', 'done', 'error', 'cancelled']
    position: int
    params: dict[str, Any]
    output_dir: str | None = None
    result: Any = None
    error_code: str | None = None
    error_detail: str | None = None
    progress: float
    stage: str | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    owner_pid: int | None = None
    starred: bool = False  # la toma elegida de su grupo (spec 006, D-4)
    group_key: str | None = None  # las tomas de un mismo texto comparten la clave


class QueueState(BaseModel):
    """Si la cola está pausada: `GET /queue`, pausar y reanudar."""

    paused: bool


class SettingOut(BaseModel):
    """Una preferencia: `GET` y `PUT /settings/{key}`. `value` es None si nunca se guardó."""

    key: str
    value: Any


class StyleOut(BaseModel):
    """Un preset del catálogo de Música (spec 011, D-2): su categoría, tonalidad, BPM, compás y si tiene muestra."""

    key: str
    category: str
    musical_key: str
    bpm: int
    time_signature: str
    caption: str
    has_sample: bool
    sample: str | None  # ruta de la muestra de 10 s, o null si aún no existe


class StylesOut(BaseModel):
    """Respuesta de `GET /music/styles`: el catálogo completo."""

    styles: list[StyleOut]


class ChooseIn(BaseModel):
    """Cuerpo de `POST /jobs/{id}/choose`: el archivo de la pista elegida."""

    file: str
