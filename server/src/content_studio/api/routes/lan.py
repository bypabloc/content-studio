"""Rutas locales de la red local (spec 032, 02 §2): el PIN, los dispositivos y los ajustes; solo en 127.0.0.1."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.lan import cert, clients, server

router = APIRouter()


class LanSettingsIn(BaseModel):
    """Cuerpo de PUT /lan/settings: solo lo que cambia."""

    enabled: bool | None = None
    address: str | None = None
    port: int | None = Field(default=None, ge=1024, le=65535)
    max_upload_mb: int | None = Field(default=None, ge=1, le=65536)
    keep_awake: bool | None = None


def _view(request: Request) -> dict[str, Any]:
    database = request.app.state.db_path
    listener = getattr(request.app.state, 'lan', None)
    running = listener.status() if listener else {'running': False, 'url': None}
    return {
        **server.read_settings(database),
        **running,
        'addresses': server.private_addresses(),
        'fingerprint': cert.fingerprint(database.parent / cert.CERT_NAME),
    }


@router.post('/lan/pairing')
def new_pin(request: Request) -> dict:
    """Un PIN de 6 dígitos para emparejar un dispositivo; vale 5 minutos y una sola vez (AC-3)."""
    return request.app.state.pairing.new()


@router.get('/lan/devices')
def devices(conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> list[dict]:
    """Los dispositivos emparejados y vigentes."""
    return clients.list_clients(conn)


@router.delete('/lan/devices/{client_id}', status_code=204)
def revoke(client_id: int, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> Response:
    """Revoca un dispositivo: su próxima petición da 401 (AC-4)."""
    if not clients.revoke(conn, client_id):
        raise ApiError(404, 'not_found')
    return Response(status_code=204)


@router.get('/lan/settings')
def read(request: Request) -> dict:
    """Ajustes, dirección, huella y si el listener escucha."""
    return _view(request)


@router.put('/lan/settings')
def update(body: LanSettingsIn, request: Request) -> dict:
    """Guarda los ajustes y, con el server en marcha, levanta o apaga el listener al momento."""
    database = request.app.state.db_path
    changes = body.model_dump(exclude_none=True)
    if 'address' in changes and not server.valid_address(changes['address']):
        raise ApiError(422, 'lan_address_invalid', address=changes['address'])
    if changes.get('enabled') and not (changes.get('address') or server.read_settings(database)['address']):
        addresses = server.private_addresses()
        if not addresses:
            raise ApiError(422, 'lan_no_address')
        changes['address'] = addresses[0]
    server.write_settings(database, changes)
    listener = getattr(request.app.state, 'lan', None)
    if listener is not None:
        try:
            listener.apply()
        except server.LanError:
            server.write_settings(database, {'enabled': False})
            raise ApiError(409, 'lan_port_busy', port=server.read_settings(database)['port']) from None
    return _view(request)
