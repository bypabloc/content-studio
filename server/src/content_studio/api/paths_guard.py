"""Archivos que la API puede servir: los de out/ y los datos de referencia (spec 004, D-5). Lo usan /files y /media."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request

from content_studio import paths
from content_studio.api.errors import ApiError


def allowed_file(request: Request, path: str) -> Path:
    """Ruta absoluta de un archivo permitido. Una relativa se cuenta desde la raíz; fuera de las carpetas permitidas
    (también con `..`) da 403, y un archivo que no existe, 404."""
    if '\x00' in path:  # un byte NUL no es parte de una ruta: resolve() lo rechaza con ValueError
        raise ApiError(403, 'forbidden_path')
    target = (paths.ROOT / path).resolve()
    if not any(target == root or root in target.parents for root in request.app.state.roots):
        raise ApiError(403, 'forbidden_path')
    if not target.is_file():
        raise ApiError(404, 'not_found')
    return target
