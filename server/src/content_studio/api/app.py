"""API local de content-studio (spec 004, D-5): FastAPI en 127.0.0.1, con token y errores con código."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from content_studio import paths
from content_studio.api import events
from content_studio.api.errors import ApiError
from content_studio.api.routes import (
    catalog,
    clean,
    diagnostics,
    editor,
    engines,
    files,
    fs,
    health,
    jobs,
    library,
    library_actions,
    library_organize,
    llm,
    media,
    mix,
    music,
    narration,
    queue,
    server_control,
    settings,
    storage,
    subtitles,
    system,
    voices,
    voices_catalog,
    voices_import,
)
from content_studio.db import connection, schema
from content_studio.jobs.worker import Worker
from content_studio.library import index as library_index
from content_studio.messages import negotiate, t
from content_studio.services.registry import SERVICES
from content_studio.subtitles import fonts

# La ventana de Tauri pide a la API desde su propio origen: http://tauri.localhost en Windows (tauri://localhost en
# macOS y Linux), y el dev server de Vite en 1420.
TAURI_ORIGINS = ['tauri://localhost', 'http://tauri.localhost', 'https://tauri.localhost', 'http://localhost:1420']


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
        payload = {'code': f'http.{exc.status_code}', 'params': {}}
    locale = negotiate(request.headers.get('accept-language'))
    payload['message'] = t(f'error.{payload["code"]}', locale, **payload['params'])
    return JSONResponse(payload, status_code=exc.status_code)


def create_app(
    db_path: Path,
    token: str,
    services: Mapping[str, Any] = SERVICES,
    worker: Worker | None = None,
    roots: Sequence[Path] | None = None,
    broker: events.Broker | None = None,
) -> FastAPI:
    """App con la base migrada y el token. `worker` (si corre) termina los procesos al cancelar un trabajo;
    `roots` son las carpetas que /files puede servir (por defecto out/, las referencias y el catálogo de voces);
    `broker` entrega los eventos de /events (el worker debe publicar en el mismo)."""
    with closing(connection.connect(db_path)) as conn:
        backups = None if db_path == Path(':memory:') else db_path.parent / 'backups'  # spec 022, D-4
        schema.migrate(conn, backups)
        library_index.backfill(conn)  # una sola vez: los trabajos anteriores a la biblioteca (spec 020, AC-1)
    app = FastAPI(title='content-studio', version='0.1.0')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=TAURI_ORIGINS,
        allow_methods=['*'],
        allow_headers=['authorization', 'content-type'],
    )
    app.state.db_path = db_path
    app.state.token = token
    app.state.stop = None
    app.state.services = services
    app.state.worker = worker
    app.state.broker = broker or events.Broker()
    app.state.dynamic_outputs = not roots
    app.state.roots = (
        [Path(root).resolve() for root in roots]
        if roots
        else [
            paths.outputs_dir(db_path).resolve(),
            paths.references_dir().resolve(),
            paths.voices_dir().resolve(),
            paths.samples_dir().resolve(),
            *fonts.font_roots(paths.DATA / 'fonts'),
        ]
    )
    app.add_exception_handler(StarletteHTTPException, _http_error)
    header_only = [Depends(_token_guard(allow_query=False))]
    app.include_router(health.router, dependencies=header_only)
    app.include_router(server_control.router, dependencies=header_only)
    app.include_router(catalog.router, dependencies=header_only)
    app.include_router(settings.router, dependencies=header_only)
    app.include_router(storage.router, dependencies=header_only)
    app.include_router(system.router, dependencies=header_only)
    app.include_router(engines.router, dependencies=header_only)
    app.include_router(diagnostics.router, dependencies=header_only)
    app.include_router(jobs.router, dependencies=header_only)
    app.include_router(queue.router, dependencies=header_only)
    app.include_router(clean.router, dependencies=header_only)
    app.include_router(subtitles.router, dependencies=header_only)
    app.include_router(mix.router, dependencies=header_only)
    app.include_router(library.router, dependencies=header_only)
    app.include_router(library_organize.router, dependencies=header_only)
    app.include_router(library_actions.router, dependencies=header_only)  # después: /library/{id} no tapa las fijas
    app.include_router(llm.router, dependencies=header_only)
    app.include_router(editor.router, dependencies=header_only)
    app.include_router(fs.router, dependencies=header_only)
    app.include_router(music.router, dependencies=header_only)
    app.include_router(narration.router, dependencies=header_only)
    app.include_router(voices.router, dependencies=header_only)
    app.include_router(voices_catalog.router, dependencies=header_only)
    app.include_router(voices_import.router, dependencies=header_only)
    # EventSource y <audio> no mandan headers: estas dos rutas también aceptan ?token=.
    query_ok = [Depends(_token_guard(allow_query=True))]
    app.include_router(events.router, dependencies=query_ok)
    app.include_router(files.router, dependencies=query_ok)
    app.include_router(media.router, dependencies=query_ok)
    app.include_router(editor.preview_router, dependencies=query_ok)
    app.include_router(library.media_router, dependencies=query_ok)
    return app
