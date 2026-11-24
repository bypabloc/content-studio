"""Búsqueda en el contenido (spec 020, D-2): lee de disco los guiones y las transcripciones; la base no guarda texto.

Para cada ítem se miran el `script.json` (solo el texto de sus segmentos), el `transcript.json` y el `words.json`
de la carpeta de su trabajo, y la transcripción en caché (013) del propio archivo. A la escala de una biblioteca
personal alcanza; si deja de alcanzar, la mejora es un índice FTS como caché (WARNING `020-busqueda-en-disco`).
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterator
from pathlib import Path

TEXT_FILES = ('script.json', 'transcript.json', 'words.json')
SECONDS = 2.0  # límite de la lectura: devuelve lo que alcanzó


def _strings(value: object) -> Iterator[str]:
    """Todas las cadenas de un JSON, en orden."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def text_of(path: Path) -> str:
    """El texto de un guion o una transcripción, en minúsculas y con los espacios normalizados; vacío si no se lee."""
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ''
    if path.name == 'script.json':
        data = data.get('segments', []) if isinstance(data, dict) else []
    return ' '.join(' '.join(_strings(data)).split()).casefold()


def _candidates(conn: sqlite3.Connection) -> Iterator[tuple[int, list[Path]]]:
    """Cada ítem con los JSON de texto que le corresponden."""
    cached: dict[str, list[Path]] = {}
    for row in conn.execute('SELECT source_path, json_path FROM transcripts'):
        cached.setdefault(row[0], []).append(Path(row[1]))
    rows = conn.execute(
        'SELECT i.id, i.path, j.output_dir FROM library_items i LEFT JOIN jobs j ON j.id = i.job_id'
    ).fetchall()
    for item_id, path, output_dir in rows:
        files = [Path(output_dir) / name for name in TEXT_FILES] if output_dir else []
        yield item_id, [*files, *cached.get(path, [])]


def matching_ids(conn: sqlite3.Connection, q: str, seconds: float = SECONDS) -> set[int]:
    """Ids de los ítems cuyo guion o transcripción contiene `q` (sin distinguir mayúsculas)."""
    needle = ' '.join(q.split()).casefold()
    deadline = time.monotonic() + seconds
    texts: dict[Path, str] = {}
    found: set[int] = set()
    for item_id, files in _candidates(conn):
        if time.monotonic() >= deadline:
            break
        for path in files:
            if path not in texts:
                texts[path] = text_of(path) if path.is_file() else ''
            if needle and needle in texts[path]:
                found.add(item_id)
                break
    return found
