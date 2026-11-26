"""PIN de emparejamiento (spec 032, D-3): 6 dígitos, válido 5 minutos, de un solo uso y con 5 intentos."""

from __future__ import annotations

import secrets
import threading
import time
from collections.abc import Callable

TTL_S = 300
MAX_FAILURES = 5


class PairingError(Exception):
    """El PIN no sirve: `pairing_invalid` (401) o `pairing_locked` (429)."""

    def __init__(self, code: str, status: int) -> None:
        """El código del catálogo de errores y su estado HTTP."""
        super().__init__(code)
        self.code = code
        self.status = status


class Pairing:
    """El PIN vigente, compartido por la app local (que lo crea) y la de la red local (que lo canjea)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Sin PIN; `clock` es falso en las pruebas."""
        self._clock = clock
        self._pin: str | None = None
        self._expires = 0.0
        self._failures = 0
        self._lock = threading.Lock()

    def new(self) -> dict[str, object]:
        """Un PIN nuevo, que reemplaza al anterior y levanta el bloqueo."""
        with self._lock:
            self._pin = f'{secrets.randbelow(10**6):06d}'
            self._expires = self._clock() + TTL_S
            self._failures = 0
            return {'pin': self._pin, 'expires_in': TTL_S}

    def redeem(self, pin: str) -> None:
        """Canjea el PIN o levanta PairingError; el quinto error lo anula hasta que se cree otro."""
        with self._lock:
            if self._failures >= MAX_FAILURES:
                raise PairingError('pairing_locked', 429)
            if self._pin is None or self._clock() >= self._expires:
                self._pin = None
                raise PairingError('pairing_invalid', 401)
            if not secrets.compare_digest(pin.encode('utf-8'), self._pin.encode('ascii')):
                self._failures += 1
                if self._failures >= MAX_FAILURES:
                    self._pin = None
                    raise PairingError('pairing_locked', 429)
                raise PairingError('pairing_invalid', 401)
            self._pin = None
