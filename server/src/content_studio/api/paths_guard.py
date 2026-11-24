"""Archivos que la API puede servir: los de out/ y los datos de referencia (spec 004, D-5). Lo usan /files y /media."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

from fastapi import Request

from content_studio import paths
from content_studio.api.errors import ApiError
from content_studio.db import connection
from content_studio.services.storage_move import follow_output_move


def _indexed(request: Request, path: str, target: Path) -> bool:
    """¿Es un archivo de la biblioteca (spec 020)? Las carpetas vigiladas están fuera de las raíces fijas."""
    database = getattr(request.app.state, 'db_path', None)
    if database is None:
        return False
    with closing(connection.connect(database)) as conn:
        row = conn.execute('SELECT 1 FROM library_items WHERE path IN (?, ?)', (path, str(target))).fetchone()
    return row is not None


def allowed_file(request: Request, path: str) -> Path:
    """Ruta absoluta de un archivo permitido. Una relativa se cuenta desde la raíz; fuera de las carpetas permitidas
    (también con `..`) da 403, y un archivo que no existe, 404."""
    if '\x00' in path:  # un byte NUL no es parte de una ruta: resolve() lo rechaza con ValueError
        raise ApiError(403, 'forbidden_path')
    target = (paths.ROOT / path).resolve()
    roots = request.app.state.roots
    if request.app.state.dynamic_outputs:
        database = request.app.state.db_path
        output = paths.outputs_dir(database).resolve()
        roots = [output, *roots[1:]]
        if not any(target.is_relative_to(root) for root in roots):
            with closing(connection.connect(database)) as conn:
                target = follow_output_move(target, conn).resolve()
    if not any(target.is_relative_to(root) for root in roots) and not _indexed(request, path, target):
        raise ApiError(403, 'forbidden_path')
    if not target.is_file():
        raise ApiError(404, 'not_found')
    return target
