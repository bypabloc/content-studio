"""Catálogo de modelos LLM locales (spec 021, D-1): GGUF, contexto, muestreo y cómo apagar el thinking. Solo stdlib."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import NamedTuple

from content_studio.db import settings

RUNTIME = 'llama-cpp'
FAMILY = 'assistant'


class LlmSpec(NamedTuple):
    """Un modelo GGUF: su repo, el archivo, tamaño, VRAM, contexto, muestreo de su card y campos extra del pedido."""

    repo: str
    file: str
    size_gb: float
    vram_gb: float
    context: int
    sampling: dict[str, float]
    extra: dict


RECOMMENDED = 'gemma-4-e4b'
MODELS: dict[str, LlmSpec] = {
    # Gemma 4: sin el token <|think|> en el sistema, el thinking queda apagado.
    'gemma-4-e4b': LlmSpec(
        'unsloth/gemma-4-E4B-it-GGUF',
        'gemma-4-E4B-it-Q4_K_M.gguf',
        5.0,
        6.0,
        8192,
        {'temperature': 1.0, 'top_p': 0.95, 'top_k': 64},
        {},
    ),
    'qwen3.5-9b': LlmSpec(
        'unsloth/Qwen3.5-9B-GGUF',
        'Qwen3.5-9B-Q4_K_M.gguf',
        5.7,
        7.0,
        8192,
        {'temperature': 0.7, 'top_p': 0.8, 'top_k': 20, 'presence_penalty': 1.5},
        {'chat_template_kwargs': {'enable_thinking': False}},
    ),
}


def gguf_path(model: str, root: Path) -> Path:
    """El GGUF que deja la receta del modelo: <motores>/<modelo>/assistant/models/<archivo>."""
    return root / model / FAMILY / 'models' / MODELS[model].file


def server_path(root: Path) -> Path:
    """El ejecutable de llama-server que deja la receta del runtime."""
    return root / RUNTIME / FAMILY / 'bin' / ('llama-server.exe' if os.name == 'nt' else 'llama-server')


def installed(model: str, root: Path) -> bool:
    """¿Está el GGUF del modelo en disco?"""
    return gguf_path(model, root).is_file()


def selected(conn: sqlite3.Connection) -> str:
    """El modelo que el usuario eligió en el selector (`select.llm.model`), o el ★ si no eligió uno válido."""
    value = settings.get(conn, 'select.llm.model', RECOMMENDED)
    return value if isinstance(value, str) and value in MODELS else RECOMMENDED


def status(root: Path) -> list[dict]:
    """Cada modelo con tamaño, VRAM, si es el ★ y si está instalado (para Motores y el selector)."""
    return [
        {
            'model': name,
            'size_gb': spec.size_gb,
            'vram_gb': spec.vram_gb,
            'recommended': name == RECOMMENDED,
            'installed': installed(name, root),
        }
        for name, spec in MODELS.items()
    ]
