"""GET, PUT y DELETE /credentials/huggingface: el token de Hugging Face sin devolverlo (spec 034, D-2)."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from content_studio import credentials
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError

router = APIRouter()
Db = Annotated[sqlite3.Connection, Depends(get_conn)]


class HuggingFaceToken(BaseModel):
    """Cuerpo de PUT: el token de lectura del usuario."""

    token: str


class Configured(BaseModel):
    """Solo dice si hay un token guardado; nunca su valor."""

    configured: bool


@router.get('/credentials/huggingface', response_model=Configured)
def read_huggingface(conn: Db) -> dict:
    """Indica si hay un token guardado."""
    return {'configured': credentials.huggingface_token(conn) is not None}


@router.put('/credentials/huggingface', response_model=Configured)
def write_huggingface(body: HuggingFaceToken, conn: Db) -> dict:
    """Guarda el token si tiene la forma de Hugging Face (hf_ seguido de caracteres)."""
    if not credentials.valid_token(body.token):
        raise ApiError(422, 'invalid_token')
    credentials.set_huggingface_token(conn, body.token)
    return {'configured': True}


@router.delete('/credentials/huggingface', response_model=Configured)
def clear_huggingface(conn: Db) -> dict:
    """Borra el token guardado."""
    credentials.clear_huggingface_token(conn)
    return {'configured': False}
