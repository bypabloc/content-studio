"""GET y PUT /settings/{key}: preferencias de la app, guardadas en la base (spec 004, D-1 y D-5)."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.schemas import SettingOut
from content_studio.db import settings as store

router = APIRouter()

# Las elecciones de los selectores van bajo este prefijo; el tema (ui.*) y los avisos (notify.*) no se restablecen.
SELECTOR_PREFIX = 'select.'


# Los secretos (secret.*) tienen su ruta propia: /credentials/huggingface (spec 034, AC-4).
def _reject_secret(key: str) -> None:
    """Ningún secreto se lee ni se escribe por la API genérica de ajustes."""
    if key.startswith('secret.'):
        raise ApiError(403, 'secret_setting')


class SettingValue(BaseModel):
    """Cuerpo de PUT /settings/{key}: cualquier valor JSON."""

    value: Any


@router.get('/settings/{key}', response_model=SettingOut)
def read_setting(key: str, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Valor de la preferencia (None si nunca se guardó)."""
    _reject_secret(key)
    return {'key': key, 'value': store.get(conn, key)}


@router.put('/settings/{key}', response_model=SettingOut)
def write_setting(key: str, body: SettingValue, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Guarda la preferencia y la devuelve."""
    _reject_secret(key)
    if key.startswith('storage.'):
        raise ApiError(422, 'storage_requires_move')
    store.set_value(conn, key, body.value)
    return {'key': key, 'value': body.value}


@router.delete('/settings')
def reset_selectors(prefix: str, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Restablece las elecciones de los selectores (`select.*`). Cualquier otro prefijo sale 422."""
    if not prefix.startswith(SELECTOR_PREFIX):
        raise ApiError(422, 'invalid_prefix', prefix=prefix)
    return {'deleted': store.delete_prefix(conn, prefix)}
