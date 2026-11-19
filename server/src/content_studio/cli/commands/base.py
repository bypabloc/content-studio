"""Comando: lo que el CLI sabe de un script (módulo, parser, textos, catálogos y estado). Solo stdlib."""

from __future__ import annotations

import importlib
from abc import ABC
from types import ModuleType
from typing import NamedTuple


class Option(NamedTuple):
    """Un valor de un flag para los menús. Con `motivo`, se muestra deshabilitado."""

    value: str
    desc: str
    reason: str | None = None


class Command(ABC):
    """Un comando del CLI. Cada subclase fija sus textos y, si los tiene, sus catálogos y su estado."""

    clave: str  # 'narration tts': la 1.ª palabra es el grupo de Typer (sin grupo si es una sola)
    module: str  # el que se lanza con -m
    parser: str  # el módulo liviano con construir_parser()
    icono: str
    titulo: str
    desc: str
    help: str  # la línea del comando en --help
    assistant: bool = False  # pregunta los flags que faltan en una terminal

    def load(self) -> ModuleType:
        """Importa el módulo liviano con el parser y los catálogos."""
        return importlib.import_module(self.parser)

    def catalog(self, mod: ModuleType) -> dict[str, list[Option]]:
        """Por flag (dest): sus opciones con descripción, para los menús."""
        return {}

    def state(self) -> list[str]:
        """Partes (markup de Rich) de la línea de estado del menú."""
        return []
