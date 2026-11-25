"""Apagado por inactividad del server compartido (spec 028, D-5): sin uso ni trabajos durante N minutos."""

from __future__ import annotations

import time
from collections.abc import Callable


class IdleClock:
    """Cuenta el tiempo sin uso. Un `hold` (una carpeta que vigila la 030) impide apagarse."""

    def __init__(self, minutes: float, clock: Callable[[], float] = time.monotonic) -> None:
        """Límite en minutos y reloj (monotónico por defecto; el de los tests es falso)."""
        self.limit = minutes * 60
        self.clock = clock
        self.last = clock()
        self.holds: set[str] = set()

    def touch(self) -> None:
        """Marca una petición o un evento de uso."""
        self.last = self.clock()

    def hold(self, name: str) -> None:
        """Impide apagarse mientras `name` esté retenido."""
        self.holds.add(name)
        self.touch()

    def release(self, name: str) -> None:
        """Suelta `name`; el reloj vuelve a contar desde ahora."""
        self.holds.discard(name)
        self.touch()

    def idle(self, busy: bool = False) -> bool:
        """True si lleva el límite sin uso, sin trabajos activos (`busy`) ni retenciones."""
        if busy or self.holds:
            return False
        return self.clock() - self.last >= self.limit
