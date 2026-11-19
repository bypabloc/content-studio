"""Etapa `validators`: tamaño por categoría con baseline (spec 003, D-2).

Mide líneas, bytes y columna más larga de cada archivo del changeset. Gana la primera categoría que casa. Un archivo del
baseline puede quedar igual o bajar, nunca crecer; cuando baja del límite, el detalle pide sacarlo del baseline.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from .. import paths

CONFIG = 'tests/validators/file-size.json'
BASELINE = 'tests/validators/file-size.baseline.json'
MEASURES = ('lines', 'bytes', 'lineLength')


def matches(rel: str, pattern: str) -> bool:
    """`*` de fnmatch ya cubre cualquier profundidad; `**/x` también casa `x` en la raíz."""
    return fnmatch.fnmatchcase(rel, pattern) or (pattern.startswith('**/') and fnmatch.fnmatchcase(rel, pattern[3:]))


def category(rel: str, config: dict) -> dict | None:
    """Categoría de tamaño del archivo `rel`, o None si está excluido o no casa con ninguna."""
    if any(matches(rel, pattern) for pattern in config.get('exclude', [])):
        return None
    for cat in config['categories']:
        if Path(rel).suffix in cat['extensions'] and any(matches(rel, pattern) for pattern in cat['include']):
            return cat
    return None


def measure(path: Path) -> dict:
    """Líneas, bytes y columna más larga de un archivo, con CRLF normalizado."""
    raw = path.read_bytes().replace(b'\r\n', b'\n')  # el CRLF del checkout en Windows no cuenta: igual en la CI
    lines = raw.decode('utf-8', errors='replace').splitlines()
    return {'lines': len(lines), 'bytes': len(raw), 'lineLength': max((len(line) for line in lines), default=0)}


def over_limit(measured: dict, limits: dict) -> list[str]:
    """Medidas que superan su límite, en texto."""
    return [f'{name} {measured[name]} > {limits[name]}' for name in MEASURES if measured[name] > limits[name]]


def load(root: Path, name: str) -> dict:
    """Lee el JSON `name` del repo; vacío si no existe."""
    path = root / name
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Etapa `validators` sobre los archivos del changeset."""
    config, baseline = load(root, CONFIG), load(root, BASELINE)
    problems, notes = [], []
    for path in files:
        if not path.is_relative_to(root):
            continue
        rel = path.relative_to(root).as_posix()
        cat = category(rel, config)
        if cat is None or not path.is_file():
            continue
        measured = measure(path)
        if rel in baseline:
            grew = [name for name in MEASURES if measured[name] > baseline[rel][name]]
            if grew:
                shown = ', '.join(f'{name} {measured[name]} > {baseline[rel][name]}' for name in grew)
                problems.append(f'{rel} ({cat["name"]}): grew past its baseline: {shown}')
            elif not over_limit(measured, cat['limits']):
                notes.append(f'{rel}: under the limit, remove it from {BASELINE}')
        elif broken := over_limit(measured, cat['limits']):
            problems.append(f'{rel} ({cat["name"]}): {", ".join(broken)}')
    return {
        'stage': 'validators',
        'status': 'fail' if problems else 'pass',
        'detail': '\n'.join(problems + notes),
    }


def write_baseline(files: list[Path], root: Path = paths.ROOT) -> int:
    """Escribe en el baseline los archivos que hoy superan su límite, con su medida. Devuelve cuántos son."""
    config = load(root, CONFIG)
    entries = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        cat = category(rel, config) if path.is_file() else None
        if cat is not None and over_limit(measure(path), cat['limits']):
            entries[rel] = measure(path)
    (root / BASELINE).write_text(json.dumps(dict(sorted(entries.items())), indent=2) + '\n', encoding='utf-8')
    return len(entries)
