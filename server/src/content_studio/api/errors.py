"""Errores de la API con código (spec 004, D-5): el cuerpo sale como {code, params, message}, con su texto."""

from __future__ import annotations

from typing import Any

from starlette.exceptions import HTTPException


class ApiError(HTTPException):
    """Error con código: `code` y `params` llenan el texto de `error.<code>` en messages/; `extra` se suma al cuerpo."""

    def __init__(self, status_code: int, code: str, extra: dict[str, Any] | None = None, **params: Any) -> None:
        """Código HTTP, código del error, campos extra del cuerpo y los parámetros de su texto."""
        super().__init__(status_code, code)
        self.code = code
        self.params = params
        self.extra = extra or {}
