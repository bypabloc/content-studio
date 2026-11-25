"""Middleware ASGI del server compartido (spec 028): marca actividad para el apagado por inactividad."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, MutableMapping
from typing import Any

from starlette.responses import JSONResponse

from content_studio.messages import negotiate, t
from content_studio.runtime.idle import IdleClock

Scope = MutableMapping[str, Any]
Asgi = Callable[[Scope, Callable[[], Awaitable[Any]], Callable[[Any], Awaitable[None]]], Awaitable[None]]

QUIET_PATHS = ('/health', '/events')  # el sondeo de la ventana y su SSE no cuentan como uso (D-5)


class ActivityGuard:
    """Cada petición real marca actividad en el reloj de inactividad."""

    def __init__(self, app: Asgi, clock: IdleClock) -> None:
        """Guarda la app y el reloj de inactividad."""
        self.app = app
        self.clock = clock

    async def __call__(
        self, scope: Scope, receive: Callable[[], Awaitable[Any]], send: Callable[[Any], Awaitable[None]]
    ) -> None:
        """Marca actividad en cada petición HTTP que no sea de sondeo."""
        if scope['type'] == 'http' and not scope['path'].startswith(QUIET_PATHS):
            self.clock.touch()
        await self.app(scope, receive, send)


class HostGuard:
    """Solo entra un Host de `hosts` (127.0.0.1 o localhost, con cualquier puerto): lo demás recibe 400 (AC-10, D-7)."""

    def __init__(self, app: Asgi, hosts: Iterable[str]) -> None:
        """Guarda la app y los Host permitidos."""
        self.app = app
        self.hosts = frozenset(hosts)

    async def __call__(
        self, scope: Scope, receive: Callable[[], Awaitable[Any]], send: Callable[[Any], Awaitable[None]]
    ) -> None:
        """Responde 400 a un Host ajeno; el resto pasa a la app."""
        if scope['type'] in ('http', 'websocket'):
            headers = dict(scope.get('headers', []))
            host = headers.get(b'host', b'').decode('latin-1').split(':')[0]
            if host not in self.hosts:
                locale = negotiate(headers.get(b'accept-language', b'').decode('latin-1') or None)
                payload = {'code': 'host_not_allowed', 'params': {}, 'message': t('error.host_not_allowed', locale)}
                await JSONResponse(payload, status_code=400)(scope, receive, send)
                return
        await self.app(scope, receive, send)
