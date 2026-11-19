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

from content_studio import paths
from content_studio.narration.styles import EMOTIONS

if TYPE_CHECKING:
    from content_studio.narration.blocks import References


@dataclass(frozen=True)
class EngineSpec:
    """Un registro por --model. venv, repo y codigo son rutas relativas a server/data/narration/ o ids de Hugging Face.
    txt: 'obligatorio' (no clona sin la transcripción), 'opcional' (clona peor sin ella) o None (no la usa)."""

    name: str
    venv: str
    module: str  # se importa recién en crear(), ya dentro del venv
    kind: str
    license: str
    commercial: bool
    txt: str | None
    ref_max_s: float
    repo: str
    code: str | None = None
    weights: float | None = None  # GiB de los pesos: con lote, el tamaño de la pasada sale de la VRAM libre
    batch: bool = False  # genera varias frases por pasada
    note: str = ''  # ranking para el menú del CLI

    def path_venv(self) -> Path:
        return paths.NARRATION / self.venv

    def installed(self) -> bool:
        return self.path_venv().exists()

    def create(self) -> TTSEngine:
        return getattr(import_module(self.module), self.kind)(self)


class TTSEngine(ABC):
    params: dict = {}  # parámetros fijos del motor, los medidos en la investigación (van al .json)
    intensity = True  # controla la intensidad de la emoción
    suggest_evaluate = False  # sin --evaluate, se sugiere

    def __init__(self, spec: EngineSpec) -> None:
        self.spec = spec

    def mode(self, text_ref: str | None) -> str:
        """Modo de clonación de un bloque sin emoción."""
        return 'cloning'

    def emotion(self, pb: dict, name: str, intensity: float, refs: References) -> None:
        """Emoción del bloque `pb`. Por defecto, la referencia del estilo que la representa (Qwen, OmniVoice)."""
        substitute = EMOTIONS[name]['ref']
        if substitute and refs.has(substitute):
            pb['ref'], pb['text_ref'] = refs(substitute)
            pb['mode'], pb['emotion'] = 'reference', mark(name, intensity)
        else:
            pb['notices'].append(f'no reference for "{name}"; generated with style {pb["style"]}')

    @abstractmethod
    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        """(audios, sr). Cada bloque trae lo que recibe el motor: 'enviar', 'ref', 'texto_ref', 'p' y 'emo'."""


def mark(name: str, intensity: float) -> dict:
    return {'name': name, 'intensity': intensity}
