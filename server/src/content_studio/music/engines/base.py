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
    """Descripción de un motor de música: su venv, su módulo y su clase."""

    name: str
    venv: str  # relativo a server/data/music/
    module: str  # se importa recién en crear(), ya dentro del venv
    kind: str
    desc: str  # texto de los selectores (la API lo expone)
    evaluates: bool = False  # su venv trae demucs: admite --evaluate
    recommended: bool = False  # la opción que la app marca con ★ (exactamente una por selector)
    max_seconds: int = 0  # la duración máxima que acepta el motor (ACE 600 s, HeartMuLa 240 s)

    def path_venv(self) -> Path:
        """Carpeta del venv administrado o externo del motor."""
        return paths.engine_root('music', self.venv, self.name) / self.venv

    def installed(self) -> bool:
        """True si el venv del motor existe."""
        return self.path_venv().exists()

    def create(self) -> MusicEngine:
        """Crea el motor, importando su módulo dentro del venv."""
        return getattr(import_module(self.module), self.kind)(self)


class MusicEngine(ABC):
    """Motor de música: genera pistas a partir de trabajos."""

    def __init__(self, spec: MusicSpec) -> None:
        """Guarda la especificación del motor."""
        self.spec = spec

    @abstractmethod
    def generate(self, jobs: Jobs, a: argparse.Namespace) -> None:
        """Carga el modelo y escribe cada salida. Si una falla, no la escribe: main() lo detecta."""
