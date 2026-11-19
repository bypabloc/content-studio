"""EspecMusica (metadatos livianos, solo stdlib) y MotorMusica, el producto que crea con su factory method."""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from content_studio import rutas

Trabajos = list[tuple[dict, Path]]  # (estilo resuelto, ruta del .wav de salida)


@dataclass(frozen=True)
class EspecMusica:
    nombre: str
    venv: str  # relativo a music/
    modulo: str  # se importa recién en crear(), ya dentro del venv
    clase: str
    desc: str  # para los menús del CLI
    evalua: bool = False  # su venv trae demucs: admite --evaluar

    def ruta_venv(self) -> Path:
        return rutas.MUSIC / self.venv

    def instalado(self) -> bool:
        return self.ruta_venv().exists()

    def crear(self) -> MotorMusica:
        return getattr(import_module(self.modulo), self.clase)(self)


class MotorMusica(ABC):
    def __init__(self, espec: EspecMusica) -> None:
        self.espec = espec

    @abstractmethod
    def generar(self, trabajos: Trabajos, a: argparse.Namespace) -> None:
        """Carga el modelo y escribe cada salida. Si una falla, no la escribe: main() lo detecta."""
