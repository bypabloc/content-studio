"""Recetas de instalación con versiones, referencias y rutas validadas."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DIRECTORY = Path(__file__).with_name('recipes')
ENGINE = re.compile(r'[a-z0-9]+(?:[.-][a-z0-9]+)*')
COMMIT = re.compile(r'[0-9a-f]{40}')
PYTHON = re.compile(r'3\.(?:10|11|12)(?:\.\d+)?')
MODULE = re.compile(r'[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*')
HF_REPO = re.compile(r'[\w.-]+/[\w.-]+')
TORCH = re.compile(r'^(torch|torchaudio|torchvision)(?:[<>=~!\[; ]|$)', re.IGNORECASE)
TORCH_PIN = re.compile(r'^(torch|torchaudio|torchvision)==[0-9][\w.+-]*(?:\s*;.*)?$', re.IGNORECASE)


@dataclass(frozen=True)
class Recipe:
    """Metadatos y pasos reproducibles de un motor."""

    engine: str
    family: str
    size_gb: float
    vram_gb: float
    cpu: bool
    license: str
    steps: tuple[dict[str, Any], ...]
    version: int = 1

    @property
    def venv(self) -> str:
        """Ruta del entorno dentro de la familia de la receta."""
        return next(str(step['path']) for step in self.steps if step['kind'] == 'venv')


def _matches(pattern: re.Pattern[str]) -> Callable[[object], bool]:
    return lambda value: isinstance(value, str) and pattern.fullmatch(value) is not None


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and '\x00' not in value


def _strings(value: object) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)


def _relative(value: object) -> bool:
    return isinstance(value, str) and all(
        re.fullmatch(r'[\w.-]+', part) and part not in ('.', '..') for part in value.split('/')
    )


def _https(value: object) -> bool:
    return isinstance(value, str) and value.startswith('https://') and _text(value[8:])


def _boolean(value: object) -> bool:
    return isinstance(value, bool)


STEP_FIELDS: dict[str, dict[str, Callable[[object], bool]]] = {
    'python': {'version': _matches(PYTHON)},
    'venv': {'path': _relative},
    'pip': {'packages': _strings},
    'git': {'url': _https, 'commit': _matches(COMMIT), 'into': _relative},
    'hf': {'repo': _matches(HF_REPO), 'revision': _matches(COMMIT), 'into': _relative},
    'verify': {'import': _matches(MODULE)},
}
OPTIONAL: dict[str, dict[str, Callable[[object], bool]]] = {
    'pip': {
        'index': lambda value: value is None or _https(value),
        'torch_backend': _text,
        'no_deps': _boolean,
        'uninstall': _boolean,
        'editable': _relative,
        'requirements': _relative,
        'exclude': _strings,
    },
    'git': {'recursive': _boolean},
    'hf': {'allow_patterns': _strings, 'ignore_patterns': _strings},
    'verify': {'paths': lambda value: isinstance(value, list) and all(_relative(path) for path in value)},
}


def _step(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError('Recipe step must be an object')
    kind = value.get('kind')
    if not isinstance(kind, str) or kind not in STEP_FIELDS:
        raise ValueError(f'Unknown recipe step: {kind}')
    required, optional = STEP_FIELDS[kind], OPTIONAL.get(kind, {})
    for field, check in required.items():
        if not check(value.get(field)):
            raise ValueError(f'Invalid {kind} step field: {field}')
    for field in value.keys() - {'kind'} - required.keys():
        if field not in optional or not optional[field](value[field]):
            raise ValueError(f'Invalid {kind} step field: {field}')
    if kind == 'pip':
        for package in value['packages']:
            if package.startswith('-') or (TORCH.match(package) and not TORCH_PIN.fullmatch(package)):
                raise ValueError(f'Invalid or unpinned pip package: {package}')
        if not (value['packages'] or value.get('editable') or value.get('requirements')):
            raise ValueError('pip step must declare packages, an editable or requirements')
    return value


def _number(value: object, minimum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError('Invalid recipe disk or VRAM size')
    return float(value)


def validate(document: object) -> Recipe:
    """Valida los metadatos y los campos de cada paso antes de ejecutar la receta."""
    if not isinstance(document, dict):
        raise ValueError('Recipe must be an object')
    engine, family = document.get('engine'), document.get('family')
    if not isinstance(engine, str) or not ENGINE.fullmatch(engine):
        raise ValueError('Invalid engine name')
    if family not in ('narration', 'music', 'system', 'transcription', 'vision'):
        raise ValueError('Invalid engine family')
    cpu, license_name = document.get('cpu'), document.get('license')
    if not isinstance(cpu, bool) or not isinstance(license_name, str) or not _text(license_name):
        raise ValueError('Invalid engine CPU support or license')
    raw_steps = document.get('steps')
    if not isinstance(raw_steps, list):
        raise ValueError('Recipe steps must be a list')
    steps = tuple(_step(value) for value in raw_steps)
    kinds = [step['kind'] for step in steps]
    if kinds[:1] != ['python'] or kinds[-1:] != ['verify'] or kinds.count('venv') != 1:
        raise ValueError('Recipe must start with python, include one venv and end with verify')
    version = document.get('version', 1)
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError('Invalid recipe version')
    return Recipe(
        engine,
        family,
        _number(document.get('size_gb'), 0.1),
        _number(document.get('vram_gb'), 0),
        cpu,
        license_name,
        steps,
        version,
    )


def load(engine: str) -> Recipe:
    """Carga la receta de un motor. El nombre debe coincidir con el archivo."""
    if not ENGINE.fullmatch(engine):
        raise ValueError('Invalid engine name')
    recipe = validate(json.loads((DIRECTORY / f'{engine}.json').read_text(encoding='utf-8')))
    if recipe.engine != engine:
        raise ValueError(f'Recipe filename mismatch: {engine}')
    return recipe


def load_all() -> list[Recipe]:
    """Carga todas las recetas incluidas en el paquete en orden estable."""
    return [load(path.stem) for path in sorted(DIRECTORY.glob('*.json'))]
