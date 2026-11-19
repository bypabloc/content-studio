"""EspecMotor (metadatos livianos, solo stdlib) y MotorTTS, el producto que crea con su factory method.

Cada motor vive en su archivo, con su `@lru_cache cargar()` a nivel de módulo (se carga una vez por proceso) y
`CACHES`, las funciones con caché que registro.liberar_todo() vacía antes de whisper y al regenerar.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

from content_studio import rutas
from content_studio.narration.estilos import EMOCIONES

if TYPE_CHECKING:
    from content_studio.narration.bloques import Referencias


@dataclass(frozen=True)
class EspecMotor:
    """Un registro por --modelo. venv, repo y codigo son rutas relativas a server/data/narration/ o ids de Hugging Face.
    txt: 'obligatorio' (no clona sin la transcripción), 'opcional' (clona peor sin ella) o None (no la usa)."""

    nombre: str
    venv: str
    modulo: str  # se importa recién en crear(), ya dentro del venv
    clase: str
    licencia: str
    comercial: bool
    txt: str | None
    ref_max_s: float
    repo: str
    codigo: str | None = None
    pesos: float | None = None  # GiB de los pesos: con lote, el tamaño de la pasada sale de la VRAM libre
    lote: bool = False  # genera varias frases por pasada
    nota: str = ''  # ranking para el menú del CLI

    def ruta_venv(self) -> Path:
        return rutas.NARRATION / self.venv

    def instalado(self) -> bool:
        return self.ruta_venv().exists()

    def crear(self) -> MotorTTS:
        return getattr(import_module(self.modulo), self.clase)(self)


class MotorTTS(ABC):
    params: dict = {}  # parámetros fijos del motor, los medidos en la investigación (van al .json)
    intensidad = True  # controla la intensidad de la emoción
    sugerir_evaluar = False  # sin --evaluar, se sugiere

    def __init__(self, espec: EspecMotor) -> None:
        self.espec = espec

    def modo(self, texto_ref: str | None) -> str:
        """Modo de clonación de un bloque sin emoción."""
        return 'clonacion'

    def emocion(self, pb: dict, nombre: str, inten: float, refs: Referencias) -> None:
        """Emoción del bloque `pb`. Por defecto, la referencia del estilo que la representa (Qwen, OmniVoice)."""
        sustituto = EMOCIONES[nombre]['ref']
        if sustituto and refs.tiene(sustituto):
            pb['ref'], pb['texto_ref'] = refs(sustituto)
            pb['modo'], pb['emocion'] = 'referencia', marca(nombre, inten)
        else:
            pb['avisos'].append(f'no hay referencia para "{nombre}"; se genera con el estilo {pb["estilo"]}')

    @abstractmethod
    def generar(self, bloques: list[dict], idioma: str) -> tuple[list, int]:
        """(audios, sr). Cada bloque trae lo que recibe el motor: 'enviar', 'ref', 'texto_ref', 'p' y 'emo'."""


def marca(nombre: str, inten: float) -> dict:
    return {'nombre': nombre, 'intensidad': inten}
