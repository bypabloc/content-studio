"""GET /files?path=: un archivo de out/ o de los datos de referencia; cualquier otra ruta da 403 (spec 004, D-5)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from content_studio.api.paths_guard import allowed_file

router = APIRouter()


@router.get('/files')
def get_file(path: str, request: Request) -> FileResponse:
    """Sirve el archivo. Una ruta relativa se cuenta desde la raíz; `..` que sale de las carpetas permitidas da 403."""
    return FileResponse(allowed_file(request, path))
