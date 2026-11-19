"""Tabla `jobs` (spec 004, D-1 y D-3): alta, lectura, filtros, siguiente en cola y actualización."""

from __future__ import annotations

import json
import sqlite3

from content_studio.db.connection import utc_now

EDITABLE = {
    'status',
    'progress',
    'stage',
    'output_dir',
    'result',
    'error_code',
    'error_detail',
    'started_at',
    'finished_at',
    'position',
}


def _decode(row: sqlite3.Row) -> dict:
    job = dict(row)
    job['params'] = json.loads(job['params'])
    return job


def insert(conn: sqlite3.Connection, kind: str, resource: str, params: dict) -> int:
    """Encola un trabajo al final y devuelve su id."""
    position = conn.execute('SELECT COALESCE(MAX(position), 0) + 1 FROM jobs').fetchone()[0]
    cursor = conn.execute(
        'INSERT INTO jobs (kind, resource, status, position, params, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (kind, resource, 'queued', position, json.dumps(params), utc_now()),
    )
    job_id = cursor.lastrowid
    assert job_id is not None  # un INSERT siempre deja el id de la fila
    return job_id


def get(conn: sqlite3.Connection, job_id: int) -> dict | None:
    """Devuelve un trabajo con `params` decodificado, o None si no existe."""
    row = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    return None if row is None else _decode(row)


def next_queued(conn: sqlite3.Connection, resource: str) -> dict | None:
    """El primer trabajo `queued` de ese recurso, por posición."""
    row = conn.execute(
        "SELECT * FROM jobs WHERE status = 'queued' AND resource = ? ORDER BY position LIMIT 1", (resource,)
    ).fetchone()
    return None if row is None else _decode(row)


def update(conn: sqlite3.Connection, job_id: int, **fields: object) -> None:
    """Cambia solo los campos dados; rechaza nombres de columna que no son editables."""
    unknown = set(fields) - EDITABLE
    if unknown:
        raise ValueError(f'non-editable columns: {sorted(unknown)}')
    if fields:
        assignments = ', '.join(f'{name} = ?' for name in fields)
        conn.execute(f'UPDATE jobs SET {assignments} WHERE id = ?', (*fields.values(), job_id))


def list_jobs(conn: sqlite3.Connection, kind: str | None = None, status: str | None = None) -> list[dict]:
    """Trabajos filtrados por tipo y/o estado, en orden de posición."""
    clauses, args = [], []
    for column, value in (('kind', kind), ('status', status)):
        if value is not None:
            clauses.append(f'{column} = ?')
            args.append(value)
    where = f'WHERE {" AND ".join(clauses)}' if clauses else ''
    return [_decode(row) for row in conn.execute(f'SELECT * FROM jobs {where} ORDER BY position', args)]
