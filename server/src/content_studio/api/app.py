"""API local de content-studio (spec 004, D-5): FastAPI en 127.0.0.1, con token y errores con código."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from content_studio import paths
from content_studio.api.errors import ApiError
from content_studio.api.routes import catalog, files, health, jobs, queue, settings
from content_studio.db import connection, schema
from content_studio.jobs.worker import Worker
from content_studio.messages import t
from content_studio.services.registry import SERVICES


def _token_guard(allow_query: bool) -> Callable[[Request], None]:
    """Exige el token en `Authorization: Bearer`; `?token=` solo si la ruta lo permite (EventSource y <audio>)."""

    def guard(request: Request) -> None:
        supplied = request.headers.get('authorization', '').removeprefix('Bearer ')
        if allow_query and not supplied:
            supplied = request.query_params.get('token', '')
        if not secrets.compare_digest(supplied.encode(), request.app.state.token.encode()):
            raise ApiError(401, 'unauthorized')

    return guard


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    """Todo error HTTP sale como {code, params, message, ...}; los ApiError traen su código y sus parámetros."""
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    if isinstance(exc, ApiError):
        payload: dict[str, Any] = {'code': exc.code, 'params': exc.params, **exc.extra}
    else:
        payload = {'code': str(exc.detail), 'params': {}}
    payload['message'] = t(payload['code'], **payload['params'])
    return JSONResponse(payload, status_code=exc.status_code)


def create_app(
    db_path: Path,
    token: str,
    services: Mapping[str, Any] = SERVICES,
    worker: Worker | None = None,
    roots: Sequence[Path] | None = None,
) -> FastAPI:
    """App con la base migrada y el token. `worker` (si corre) termina los procesos al cancelar un trabajo;
    `roots` son las carpetas que /files puede servir (por defecto out/ y los datos de referencia)."""
    with closing(connection.connect(db_path)) as conn:
        schema.migrate(conn)
    app = FastAPI(title='content-studio', version='0.1.0')
    app.state.db_path = db_path
    app.state.token = token
    app.state.services = services
    app.state.worker = worker
    app.state.roots = (
        [Path(root).resolve() for root in roots] if roots else [paths.OUT.resolve(), paths.REFERENCE.resolve()]
    )
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.include_router(health.router, dependencies=[Depends(_token_guard(allow_query=False))])
    app.include_router(catalog.router, dependencies=[Depends(_token_guard(allow_query=False))])
    app.include_router(settings.router, dependencies=[Depends(_token_guard(allow_query=False))])
    app.include_router(jobs.router, dependencies=[Depends(_token_guard(allow_query=False))])
    app.include_router(queue.router, dependencies=[Depends(_token_guard(allow_query=False))])
    app.include_router(files.router, dependencies=[Depends(_token_guard(allow_query=True))])
    return app
