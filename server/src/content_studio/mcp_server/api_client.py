"""Cliente HTTP mínimo hacia la API local (spec 029): urllib y el token de la instalación, sin dependencias.

Un error de la API llega como ApiFailure con su estado y su cuerpo JSON; un server que no responde, como OSError.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class ApiFailure(Exception):
    """Un error de la API: el estado HTTP y el cuerpo JSON (un 422 trae `errors`; un 404, `code`)."""

    def __init__(self, status: int, body: Any) -> None:
        """El estado HTTP y el cuerpo JSON del error."""
        super().__init__(f'HTTP {status}')
        self.status = status
        self.body = body


class Api:
    """Las llamadas de las herramientas: JSON con el Bearer del server compartido."""

    def __init__(self, base_url: str, token: str, *, language: str = 'es', timeout: float = 30) -> None:
        """Una conexión a la API en `base_url`, con el token de la instalación."""
        self.base_url = base_url.rstrip('/')
        self._token = token
        self._language = language
        self._timeout = timeout

    def get(self, path: str) -> Any:
        """GET de `path`: el JSON de la respuesta."""
        return self._call('GET', path, None)

    def post(self, path: str, body: Any = None) -> Any:
        """POST de `path` con `body`: el JSON de la respuesta."""
        return self._call('POST', path, body)

    def _call(self, method: str, path: str, body: Any) -> Any:
        data = json.dumps(body).encode('utf-8') if body is not None else None
        request = urllib.request.Request(f'{self.base_url}{path}', data=data, method=method)
        request.add_header('Authorization', f'Bearer {self._token}')
        request.add_header('Accept-Language', self._language)
        if data is not None:
            request.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            raise ApiFailure(error.code, _decode(error.read())) from None
        return _decode(raw)


def _decode(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode('utf-8'))
    except ValueError:
        return None
