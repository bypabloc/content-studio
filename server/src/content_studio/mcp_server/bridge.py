"""Puente MCP → API (spec 029, AC-2 a AC-8): cada herramienta es una llamada a la API del server compartido.

El puente no importa el SDK: `sdk.py` lo llama con `call()` y publica el resultado. Las llamadas bloqueantes van en
un hilo para no frenar el protocolo.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from content_studio import gpu_lock, paths
from content_studio.common.checkout import main_checkout
from content_studio.db import connection, settings
from content_studio.mcp_server import tools
from content_studio.mcp_server.api_client import Api, ApiFailure
from content_studio.messages import t
from content_studio.runtime import discovery, instance

TERMINAL = ('done', 'error', 'cancelled')
DEFAULT_WAIT_S = 60
MAX_WAIT_S = 300
LOCALES = ('es', 'en', 'pt')

Notify = Callable[[float, float | None, str | None], Awaitable[None]]


@dataclass
class ToolResult:
    """Lo que la herramienta devuelve: el texto para el modelo, el `structuredContent` y los recursos de salida."""

    text: str
    structured: dict[str, Any]
    is_error: bool = False
    links: list[dict[str, str]] = field(default_factory=list)


class Bridge:
    """Traduce las herramientas a llamadas a la API del server de esta instalación (AC-2)."""

    def __init__(
        self,
        db: Path,
        *,
        api: Callable[[], Api] | None = None,
        poll_s: float = 1.0,
        main: Path | None = None,
    ) -> None:
        """El puente de esta base; `api` y `main` se cambian en las pruebas."""
        self._db = db
        self._api = api or self._connect
        self._poll_s = poll_s
        self._main = main or main_checkout(paths.ROOT)

    async def call(self, name: str, args: dict[str, Any], notify: Notify | None = None) -> ToolResult:
        """Ejecuta la herramienta `name`; los errores vuelven como `ToolResult` con `is_error`, no como excepción."""
        locale = await asyncio.to_thread(self._locale)
        try:
            if name == 'studio_wait_job':
                return await self._wait(args, notify, locale)
            return await asyncio.to_thread(self._sync, name, args, locale)
        except tools.ToolError as error:
            return _failure(error.code, error.params, locale)
        except ApiFailure as failure:
            return _api_failure(failure, locale)
        except OSError:  # el server no responde ni arranca: el log dice por qué (AC-2)
            return _failure('server_unavailable', {'log': str(instance.log_path())}, locale)

    def _sync(self, name: str, args: dict[str, Any], locale: str) -> ToolResult:  # noqa: ARG002
        api = self._api()
        if name == 'studio_capabilities':
            return _ok(self._capabilities(api))
        if name == 'studio_get_job':
            return self._get_jobs(api, args)
        if name == 'studio_cancel_job':
            job_id = _job_id(args)
            api.post(f'/jobs/{job_id}/cancel')
            view, outputs = self._snapshot(api, job_id)
            return _ok(view, outputs)
        if name == 'studio_watch_folder':
            body = {
                'path': args.get('path', ''),
                'kind': args.get('kind', ''),
                'params': args.get('params') or {},
                'keep_awake': args.get('keep_awake', True),
            }
            return _ok(api.post('/inbox/folders', body))
        kind, params = tools.build_job(name, args)
        return _ok(tools.job_view(api.post('/jobs', {'kind': kind, 'params': params}), []))

    def _capabilities(self, api: Api) -> dict[str, Any]:
        from content_studio.media.formats import TARGETS
        from content_studio.services.registry import SERVICES

        return {
            'narration': api.get('/catalog/narration'),
            'music': api.get('/catalog/music'),
            'conversion_targets': sorted(TARGETS),
            'job_kinds': sorted(kind for kind in SERVICES if kind in tools.MCP_KINDS),
        }

    def _get_jobs(self, api: Api, args: dict[str, Any]) -> ToolResult:
        if args.get('job_id') is not None:
            view, outputs = self._snapshot(api, _job_id(args))
            return _ok({'job': view}, outputs)
        jobs = api.get('/jobs')[: tools.LIST_LIMIT]
        return _ok({'jobs': [tools.job_view(job, [], self._waiting_on(job)) for job in jobs]})

    def _snapshot(self, api: Api, job_id: int) -> tuple[dict[str, Any], list[str]]:
        job = api.get(f'/jobs/{job_id}')
        outputs = api.get(f'/jobs/{job_id}/outputs') if job['status'] == 'done' else []
        return tools.job_view(job, outputs, self._waiting_on(job)), outputs

    def _waiting_on(self, job: dict[str, Any]) -> str | None:
        """Quién tiene la GPU cuando un trabajo de GPU sigue en cola (AC-7); None en los demás casos."""
        if job['status'] != 'queued' or job.get('resource') != 'gpu':
            return None
        owner = gpu_lock.read(self._main)
        if owner is None:
            return None
        work = owner.get('work') or 'another job'
        return f'pid {owner.get("pid")}: {work}'

    async def _wait(self, args: dict[str, Any], notify: Notify | None, locale: str) -> ToolResult:  # noqa: ARG002
        job_id = _job_id(args)
        timeout = min(max(float(args.get('timeout_s', DEFAULT_WAIT_S)), 0.0), float(MAX_WAIT_S))
        api = await asyncio.to_thread(self._api)
        deadline = time.monotonic() + timeout
        while True:
            view, outputs = await asyncio.to_thread(self._snapshot, api, job_id)
            if notify is not None:
                await notify(float(view['progress']), 1.0, view['stage'] or view['status'])
            if view['status'] in TERMINAL:
                return _ok(view, outputs)
            if time.monotonic() >= deadline:  # vencer no es un error: vuelve el estado actual (AC-5)
                return _ok({**view, 'timed_out': True}, outputs)
            await asyncio.sleep(self._poll_s)

    def _connect(self) -> Api:
        info = instance.ensure_running(self._db)
        return Api(info['url'], discovery.token(self._db.parent), language=self._locale())

    def _locale(self) -> str:
        """El idioma de la app (`ui.language`), para los mensajes de la herramienta; español si no hay."""
        try:
            conn = connection.connect(self._db)
        except (sqlite3.Error, OSError):
            return 'es'
        try:
            value = settings.get(conn, 'ui.language', 'es')
        except sqlite3.Error:
            value = 'es'
        finally:
            conn.close()
        return value if value in LOCALES else 'es'


def _job_id(args: dict[str, Any]) -> int:
    value = args.get('job_id')
    if not isinstance(value, int) or isinstance(value, bool):
        raise tools.ToolError('job_id_required')
    return value


def _ok(view: dict[str, Any], outputs: list[str] | tuple[()] = ()) -> ToolResult:
    return ToolResult(
        text=json.dumps(view, ensure_ascii=False),
        structured=view,
        links=[tools.resource_link(path) for path in outputs],
    )


def _failure(code: str, params: dict[str, Any], locale: str) -> ToolResult:
    message = t(f'error.{code}', locale, **params)
    return ToolResult(
        text=message,
        structured={'error': {'code': code, 'params': params, 'message': message}},
        is_error=True,
    )


def _api_failure(failure: ApiFailure, locale: str) -> ToolResult:
    body = failure.body if isinstance(failure.body, dict) else {}
    if failure.status == 422 and isinstance(body.get('errors'), list):
        errors = [
            {
                'code': item.get('code'),
                'params': item.get('params', {}),
                'message': t(f'error.{item.get("code")}', locale, **item.get('params', {})),
            }
            for item in body['errors']
        ]
        message = '; '.join(item['message'] for item in errors) or 'validation_failed'
        return ToolResult(
            text=message,
            structured={'error': {'code': 'validation_failed', 'params': {}, 'message': message}, 'errors': errors},
            is_error=True,
        )
    code = str(body.get('code') or f'http_{failure.status}')
    message = str(body.get('message') or code)
    return ToolResult(
        text=message,
        structured={'error': {'code': code, 'params': body.get('params', {}), 'message': message}},
        is_error=True,
    )


def run_stdio(db: Path) -> None:
    """Sirve las herramientas por stdio hasta que el cliente cierra (`studio mcp`, AC-1 y AC-2)."""
    from content_studio.mcp_server import sdk

    asyncio.run(sdk.serve_stdio(sdk.build_server(Bridge(db))))
