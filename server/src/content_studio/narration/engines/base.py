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
    note: str = ''  # ranking para los selectores (la API lo expone)
    recommended: bool = False  # la opción que la app marca con ★ (exactamente una por selector)

    def path_venv(self) -> Path:
        """Carpeta del venv administrado o externo del motor."""
        return paths.engine_root('narration', self.venv, self.name) / self.venv

    def installed(self) -> bool:
        """True si el venv del motor existe."""
        return self.path_venv().exists()

    def create(self) -> TTSEngine:
        """Crea el motor, importando su módulo dentro del venv."""
        return getattr(import_module(self.module), self.kind)(self)


class TTSEngine(ABC):
    """Motor TTS: clona una voz y genera el audio de cada bloque."""

    params: dict = {}  # parámetros fijos del motor, los medidos en la investigación (van al .json)
    intensity = True  # controla la intensidad de la emoción
    suggest_evaluate = False  # sin --evaluate, se sugiere

    def __init__(self, spec: EngineSpec) -> None:
        """Guarda la especificación del motor."""
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
    """Marca de emoción de un bloque: su nombre e intensidad."""
    return {'name': name, 'intensity': intensity}
