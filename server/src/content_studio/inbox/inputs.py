"""Qué parámetro recibe el archivo que se suelta en cada carpeta, por tipo de trabajo (spec 030, 02 §4.1)."""

from __future__ import annotations

from pathlib import Path

INPUT_PARAM = {
    'media.convert': 'input',
    'media.normalize': 'input',
    'clean.analyze': 'input',
    'narration': 'file',  # un guion (.txt) por trabajo, en lista
}
LIST_PARAMS = frozenset({'narration'})


def input_value(kind: str, path: Path) -> str | list[str]:
    """El valor del parámetro de entrada para `path`: una ruta, o una lista de una si el tipo la pide así."""
    return [str(path)] if kind in LIST_PARAMS else str(path)
