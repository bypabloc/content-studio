"""Lo común de las tareas de subtítulos (spec 021, D-4): el proyecto, los límites del estilo, los lotes y el schema."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator, Sequence
from typing import Any, TypeVar

from content_studio.db import subtitle_projects
from content_studio.llm import prompts
from content_studio.subtitles.segment import wrap_lines

DEFAULT_LIMITS = (42, 2)  # los de segment(): 42 caracteres y 2 renglones
BATCH = 30
CONTEXT = 5
SCHEMA = {
    'type': 'object',
    'properties': {
        'cues': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {'id': {'type': 'integer'}, 'text': {'type': 'string', 'minLength': 1}},
                'required': ['id', 'text'],
            },
        }
    },
    'required': ['cues'],
}
Item = TypeVar('Item')


def prepare(conn: sqlite3.Connection, params: dict) -> tuple[dict, None]:
    """Agrega el documento del proyecto; sin proyecto no agrega nada y `validate_project` lo rechaza."""
    project_id = params.get('project_id')
    project = subtitle_projects.get(conn, project_id) if isinstance(project_id, int) else None
    if project is None:
        return params, None
    return {**params, 'doc': project['doc_path']}, None


def validate_project(params: dict) -> list[dict]:
    """El trabajo necesita el documento de un proyecto existente."""
    if not params.get('doc'):
        return [{'code': 'subtitle_project_not_found', 'params': {'project_id': params.get('project_id')}}]
    return []


def limits(doc: dict) -> tuple[int, int]:
    """Caracteres por renglón y renglones del estilo del documento."""
    style = doc.get('style') or {}
    return int(style.get('max_chars', DEFAULT_LIMITS[0])), int(style.get('max_lines', DEFAULT_LIMITS[1]))


def fits(text: str, limit: tuple[int, int]) -> bool:
    """¿El texto entra en el estilo sin cortar palabras?"""
    return len(wrap_lines(text.split(), limit[0])) <= limit[1]


def batches(
    items: Sequence[Item], size: int = BATCH, context: int = CONTEXT
) -> Iterator[tuple[list[Item], list[Item]]]:
    """Lotes de `size` con los `context` anteriores, para que el modelo no traduzca cada cue suelto."""
    for start in range(0, len(items), size):
        yield list(items[start : start + size]), list(items[max(0, start - context) : start])


def message(name: str, items: list[dict], **values: object) -> list[dict]:
    """El pedido: el prompt y, al final, los cues en JSON después de `CUES:`."""
    text = prompts.render(name, **values) + '\n\nCUES:\n' + json.dumps(items, ensure_ascii=False, indent=1)
    return [{'role': 'user', 'content': text}]


def ids_check(ids: Sequence[int]) -> Callable[[dict], list[str]]:
    """Exige exactamente los id del lote: ni faltan ni sobran."""

    def check(answer: dict[str, Any]) -> list[str]:
        got = [item['id'] for item in answer['cues']]
        missing, extra = sorted(set(ids) - set(got)), sorted(set(got) - set(ids))
        found = [f'$.cues: missing ids {missing}'] if missing else []
        return found + ([f'$.cues: unknown ids {extra}'] if extra else [])

    return check
