"""GET /files?path=: un archivo de out/ o de los datos de referencia; cualquier otra ruta da 403 (spec 004, D-5)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from content_studio import paths
from content_studio.api.errors import ApiError

router = APIRouter()


@router.get('/files')
def get_file(path: str, request: Request) -> FileResponse:
    """Sirve el archivo. Una ruta relativa se cuenta desde la raíz; `..` que sale de las carpetas permitidas da 403."""
    target = (paths.ROOT / path).resolve()
    if not any(target == root or root in target.parents for root in request.app.state.roots):
        raise ApiError(403, 'forbidden_path')
    if not target.is_file():
        raise ApiError(404, 'not_found')
    return FileResponse(target)
