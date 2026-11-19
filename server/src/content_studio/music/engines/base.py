"""EspecMusica (metadatos livianos, solo stdlib) y MotorMusica, el producto que crea con su factory method."""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from content_studio import paths

Jobs = list[tuple[dict, Path]]  # (estilo resuelto, ruta del .wav de salida)


@dataclass(frozen=True)
class MusicSpec:
    name: str
    venv: str  # relativo a server/data/music/
    module: str  # se importa recién en crear(), ya dentro del venv
    kind: str
    desc: str  # para los menús del CLI
    evaluates: bool = False  # su venv trae demucs: admite --evaluate

    def path_venv(self) -> Path:
        return paths.MUSIC / self.venv

    def installed(self) -> bool:
        return self.path_venv().exists()

    def create(self) -> MusicEngine:
        return getattr(import_module(self.module), self.kind)(self)


class MusicEngine(ABC):
    def __init__(self, spec: MusicSpec) -> None:
        self.spec = spec

    @abstractmethod
    def generate(self, jobs: Jobs, a: argparse.Namespace) -> None:
        """Carga el modelo y escribe cada salida. Si una falla, no la escribe: main() lo detecta."""
