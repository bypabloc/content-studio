"""Cola de la API (spec 004, D-3 y D-5): estado, pausar, reanudar y reordenar; cada cambio sale como evento `queue`."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.jobs import queue

router = APIRouter()


class QueueOrder(BaseModel):
    """Cuerpo de PUT /queue/order: los ids de los trabajos en el orden en que deben correr."""

    ids: list[int]


def _announce(request: Request, data: dict) -> None:
    """Publica el cambio de la cola a los suscriptores de /events."""
    request.app.state.broker.publish({'type': 'queue', 'data': data})


@router.get('/queue')
def queue_state(conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Si la cola está pausada."""
    return {'paused': queue.paused(conn)}


@router.post('/queue/pause')
def pause(request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Pausa la cola: el worker no toma trabajos nuevos."""
    queue.pause(conn)
    _announce(request, {'paused': True})
    return {'paused': True}


@router.post('/queue/resume')
def resume(request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Reanuda la cola."""
    queue.resume(conn)
    _announce(request, {'paused': False})
    return {'paused': False}


@router.put('/queue/order')
def reorder(body: QueueOrder, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Reordena los trabajos según la lista dada."""
    queue.reorder(conn, body.ids)
    _announce(request, {'order': body.ids})
    return {'ids': body.ids}
