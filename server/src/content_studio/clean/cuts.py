"""Cortes del limpiador (spec 013, D-3 y D-4): `cuts.json` y su replanificación. Solo stdlib."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from content_studio.clean.plan import Cut, Span, plan


def file_for(folder: Path) -> Path:
    """Dónde va `cuts.json` dentro de la carpeta del trabajo."""
    return folder / 'cuts.json'


def save(folder: Path, document: dict) -> None:
    """Guarda el documento de cortes (parámetros y cortes) en la carpeta del trabajo."""
    folder.mkdir(parents=True, exist_ok=True)
    file_for(folder).write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')


def load(folder: Path) -> dict:
    """Lee el documento de cortes de la carpeta del trabajo."""
    return json.loads(file_for(folder).read_text(encoding='utf-8'))


def _overlaps(a: Cut, b: Cut) -> bool:
    return a['start'] < b['end'] and b['start'] < a['end']


def replan(
    words: Sequence[Span],
    duration: float,
    min_gap: float,
    padding: float,
    edges: bool,
    previous: Sequence[Cut],
) -> list[Cut]:
    """Recalcula los cortes sin editar con los nuevos parámetros, y conserva los editados a mano (AC-7).

    Un corte calculado que se solapa con uno editado cede el paso al editado.
    """
    kept = [c for c in previous if c.get('edited')]
    added = plan(words, duration, min_gap=min_gap, padding=padding, edges=edges)
    added = [c for c in added if not any(_overlaps(c, k) for k in kept)]
    return sorted(kept + added, key=lambda c: c['start'])
