"""Búsqueda y filtros de la biblioteca (spec 020, D-2): SQL sobre `library_items` con `jobs`, etiquetas y proyectos.

`q` busca en el nombre del archivo y en las etiquetas (`LIKE`); con `content`, también en el texto de los guiones y
transcripciones en disco (`text_search`). La carpeta del trabajo no cuenta: su nombre lleva parte del guion.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import PurePath

from content_studio.library import text_search

SORTS = {
    'date': 'i.mtime DESC, i.id DESC',
    'name': 'lower(basename(i.path)), i.id',
    'size': 'i.size DESC, i.id DESC',
    'duration': 'i.duration IS NULL, i.duration DESC, i.id DESC',
}
PAGE_SIZE = 100


def _basename(path: str) -> str:
    """Nombre del archivo de una ruta de Windows o POSIX."""
    return PurePath(path.replace('\\', '/')).name


def _day(value: str, end: bool = False) -> float:
    """`AAAA-MM-DD` como segundos desde la época, al inicio del día (o al final con `end`)."""
    day = datetime.fromisoformat(value)
    return (day + timedelta(days=1) if end else day).timestamp()


def _tags(conn: sqlite3.Connection, ids: list[int]) -> dict[int, list[str]]:
    marks = ','.join('?' * len(ids))
    rows = conn.execute(
        f'SELECT it.item_id, t.name FROM item_tags it JOIN tags t ON t.id = it.tag_id WHERE it.item_id IN ({marks}) '
        'ORDER BY t.name',
        ids,
    )
    found: dict[int, list[str]] = {}
    for item_id, name in rows:
        found.setdefault(item_id, []).append(name)
    return found


def search(
    conn: sqlite3.Connection,
    *,
    q: str | None = None,
    content: bool = False,
    kind: str | None = None,
    media_type: str | None = None,
    tag: str | None = None,
    project: int | None = None,
    folder: int | None = None,
    origin: str | None = None,
    starred: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_dur: float | None = None,
    max_dur: float | None = None,
    sort: str = 'date',
    page: int = 1,
    page_size: int = PAGE_SIZE,
) -> dict:
    """`{items, total}` de la página pedida. ValueError si el orden no existe."""
    if sort not in SORTS:
        raise ValueError(f'unknown sort: {sort}')
    conn.create_function('basename', 1, _basename, deterministic=True)
    clauses: list[str] = []
    args: list[object] = []
    if q:
        like = f'%{q}%'
        tagged = 'SELECT it.item_id FROM item_tags it JOIN tags t ON t.id = it.tag_id WHERE t.name LIKE ?'
        text = f'basename(i.path) LIKE ? OR i.id IN ({tagged})'
        args += [like, like]
        found = text_search.matching_ids(conn, q) if content else set()
        if found:
            text += f' OR i.id IN ({",".join(str(int(item)) for item in found)})'
        clauses.append(f'({text})')
    filters = [
        (kind, 'i.kind = ?'),
        (media_type, 'i.media_type = ?'),
        (origin, 'i.origin = ?'),
        (folder, 'i.folder_id = ?'),
        (tag, 'i.id IN (SELECT it.item_id FROM item_tags it JOIN tags t ON t.id = it.tag_id WHERE t.name = ?)'),
        (project, 'i.id IN (SELECT item_id FROM project_items WHERE project_id = ?)'),
        (min_dur, 'i.duration >= ?'),
        (max_dur, 'i.duration <= ?'),
        (_day(date_from) if date_from else None, 'i.mtime >= ?'),
        (_day(date_to, end=True) if date_to else None, 'i.mtime < ?'),
    ]
    for value, clause in filters:
        if value is not None:
            clauses.append(clause)
            args.append(value)
    if starred is not None:
        clauses.append('COALESCE(j.starred, 0) = ?')
        args.append(int(starred))
    where = f'WHERE {" AND ".join(clauses)}' if clauses else ''
    base = f'FROM library_items i LEFT JOIN jobs j ON j.id = i.job_id {where}'
    total = conn.execute(f'SELECT COUNT(*) {base}', args).fetchone()[0]
    rows = conn.execute(
        f'SELECT i.*, basename(i.path) AS name, COALESCE(j.starred, 0) AS starred, j.group_key {base} '
        f'ORDER BY {SORTS[sort]} LIMIT ? OFFSET ?',
        [*args, page_size, (max(page, 1) - 1) * page_size],
    ).fetchall()
    items = [dict(row) for row in rows]
    tags = _tags(conn, [item['id'] for item in items]) if items else {}
    for item in items:
        item['starred'] = bool(item['starred'])
        item['missing'] = bool(item['missing'])
        item['tags'] = tags.get(item['id'], [])
    return {'items': items, 'total': total}
