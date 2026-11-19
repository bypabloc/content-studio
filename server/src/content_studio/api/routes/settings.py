"""GET y PUT /settings/{key}: preferencias de la app, guardadas en la base (spec 004, D-1 y D-5)."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.schemas import SettingOut
from content_studio.db import settings as store

router = APIRouter()


class SettingValue(BaseModel):
    """Cuerpo de PUT /settings/{key}: cualquier valor JSON."""

    value: Any


@router.get('/settings/{key}', response_model=SettingOut)
def read_setting(key: str, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Valor de la preferencia (None si nunca se guardó)."""
    return {'key': key, 'value': store.get(conn, key)}


@router.put('/settings/{key}', response_model=SettingOut)
def write_setting(key: str, body: SettingValue, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Guarda la preferencia y la devuelve."""
    store.set_value(conn, key, body.value)
    return {'key': key, 'value': body.value}
