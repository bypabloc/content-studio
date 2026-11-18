"""Comando: lo que el CLI sabe de un script (módulo, parser, textos, catálogos y estado). Solo stdlib."""

from __future__ import annotations

import importlib
from abc import ABC
from types import ModuleType
from typing import NamedTuple


class Opcion(NamedTuple):
    """Un valor de un flag para los menús. Con `motivo`, se muestra deshabilitado."""

    valor: str
    desc: str
    motivo: str | None = None


class Comando(ABC):
    """Un comando del CLI. Cada subclase fija sus textos y, si los tiene, sus catálogos y su estado."""

    clave: str  # 'narration tts': la 1.ª palabra es el grupo de Typer (sin grupo si es una sola)
    modulo: str  # el que se lanza con -m
    parser: str  # el módulo liviano con construir_parser()
    icono: str
    titulo: str
    desc: str
    ayuda: str  # la línea del comando en --help
    asistente: bool = False  # pregunta los flags que faltan en una terminal

    def cargar(self) -> ModuleType:
        """Importa el módulo liviano con el parser y los catálogos."""
        return importlib.import_module(self.parser)

    def catalogo(self, mod: ModuleType) -> dict[str, list[Opcion]]:
        """Por flag (dest): sus opciones con descripción, para los menús."""
        return {}

    def estado(self) -> list[str]:
        """Partes (markup de Rich) de la línea de estado del menú."""
        return []
