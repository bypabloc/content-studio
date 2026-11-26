"""MCP por Streamable HTTP en /mcp del listener de la red local (spec 032, D-6 y AC-8).

Cada petición trae el token del dispositivo: la puerta lo valida, rechaza un `Origin` ajeno y lo deja en
`current_token`, que el puente usa para llamar a la app de la red local con ese mismo token. Así el MCP remoto pasa por
las mismas guardas que la API (sus trabajos, sus subidas y nada de administración). El SDK se importa dentro de `mount`.
"""

from __future__ import annotations

import ssl
from collections.abc import Awaitable, Callable, MutableMapping
from contextlib import closing
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from content_studio.db import connection
from content_studio.lan import clients
from content_studio.messages import negotiate, t

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Any]]
Send = Callable[[Any], Awaitable[None]]

current_token: ContextVar[str] = ContextVar('lan_device_token', default='')


class DeviceGate:
    """Deja pasar al MCP solo a un dispositivo vigente con permiso `jobs` y sin un `Origin` ajeno."""

    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]], db: Path, origin: str) -> None:
        """La app del SDK, la base de los dispositivos y el único `Origin` aceptado (la URL del listener)."""
        self.app = app
        self.db = db
        self.origin = origin

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """403 con un `Origin` ajeno, 401 sin un dispositivo vigente; si no, el MCP con el token a mano."""
        import anyio

        headers = Headers(scope=scope)
        origin = headers.get('origin')
        if origin and origin != self.origin:
            await _refuse(scope, receive, send, 403, {'code': 'origin_not_allowed', 'params': {}}, headers)
            return
        token = headers.get('authorization', '').removeprefix('Bearer ')
        client = await anyio.to_thread.run_sync(self._authenticate, token)
        if client is None or 'jobs' not in client['scopes']:
            await _refuse(scope, receive, send, 401, {'code': 'unauthorized', 'params': {}}, headers)
            return
        reset = current_token.set(token)
        try:
            await self.app(scope, receive, send)
        finally:
            current_token.reset(reset)

    def _authenticate(self, token: str) -> dict | None:
        with closing(connection.connect(self.db)) as conn:
            return clients.authenticate(conn, token)


async def _refuse(
    scope: Scope, receive: Receive, send: Send, status: int, error: dict[str, Any], headers: Headers
) -> None:
    locale = negotiate(headers.get('accept-language'))
    payload = {**error, 'message': t(f'error.{error["code"]}', locale)}
    await JSONResponse(payload, status_code=status)(scope, receive, send)


def mount(app: Any, lan_url: str) -> None:
    """Monta /mcp en la app de la red local, sin estado por sesión, con el ciclo de vida del SDK."""
    from mcp.server.streamable_http_manager import StreamableHTTPASGIApp, StreamableHTTPSessionManager
    from starlette.routing import Route

    from content_studio.mcp_server import sdk
    from content_studio.mcp_server.api_client import Api
    from content_studio.mcp_server.bridge import Bridge

    context = ssl.create_default_context(cafile=str(app.state.cert_path))
    context.check_hostname = False  # la confianza es el certificado propio, no el nombre: la IP puede cambiar
    database = app.state.db_path
    bridge = Bridge(database, api=lambda: Api(lan_url, current_token.get(), context=context), remote=True)
    manager = StreamableHTTPSessionManager(app=sdk.build_server(bridge), stateless=True)
    gate = DeviceGate(StreamableHTTPASGIApp(manager), database, lan_url)
    app.router.routes.append(Route('/mcp', endpoint=gate, methods=['GET', 'POST', 'DELETE']))
    app.router.lifespan_context = lambda _app: manager.run()
