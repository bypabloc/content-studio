"""POST /uploads (spec 032, AC-6): un dispositivo de la red local sube un archivo para usarlo como entrada.

El cuerpo es el archivo crudo (`application/octet-stream`) y el nombre va en `?name=`: se escribe por partes y el tope
de `api.lan.max_upload_mb` corta la subida con 413 sin dejar el archivo a medias.
"""

from __future__ import annotations

import secrets
from contextlib import closing

from fastapi import APIRouter, Query, Request

from content_studio import paths
from content_studio.api.errors import ApiError
from content_studio.db import connection
from content_studio.lan import guard

router = APIRouter()


@router.post('/uploads', status_code=201)
async def upload(request: Request, name: str = Query(min_length=1, max_length=200)) -> dict:
    """Guarda el archivo en `<salidas>/uploads/<dispositivo>/` y devuelve su `upload:<id>`."""
    client = request.state.client
    limit = request.app.state.max_upload_bytes
    max_mb = limit // (1024 * 1024)
    declared = request.headers.get('content-length', '')
    if declared.isdigit() and int(declared) > limit:
        raise ApiError(413, 'upload_too_large', max_mb=max_mb)
    database = request.app.state.db_path
    folder = paths.outputs_dir(database) / 'uploads' / str(client['id'])
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'{secrets.token_hex(4)}-{guard.safe_name(name)}'
    size = 0
    with target.open('wb') as out:
        async for chunk in request.stream():
            size += len(chunk)
            if size > limit:
                break
            out.write(chunk)
    if size > limit:
        target.unlink(missing_ok=True)
        raise ApiError(413, 'upload_too_large', max_mb=max_mb)
    with closing(connection.connect(database)) as conn:
        upload_id = guard.record_upload(conn, client['id'], target, size)
    return {'id': upload_id, 'ref': f'{guard.PREFIX}{upload_id}', 'name': target.name, 'size': size}
