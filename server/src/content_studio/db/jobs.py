"""Tabla `jobs` (spec 004 D-1 y D-3; spec 006 D-4): alta, lectura, filtros, cola, actualización y elegida."""

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
    'client_id',  # el dispositivo de la red local que lo pidió (spec 032, AC-7)
}


def _decode(row: sqlite3.Row) -> dict:
    job = dict(row)
    job['params'] = json.loads(job['params'])
    job['result'] = json.loads(job['result']) if job.get('result') else None
    job['starred'] = bool(job['starred'])
    return job


def insert(conn: sqlite3.Connection, kind: str, resource: str, params: dict, group_key: str | None = None) -> int:
    """Encola un trabajo al final y devuelve su id. `group_key` une las tomas de un mismo texto."""
    position = conn.execute('SELECT COALESCE(MAX(position), 0) + 1 FROM jobs').fetchone()[0]
    cursor = conn.execute(
        'INSERT INTO jobs (kind, resource, status, position, params, created_at, group_key) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (kind, resource, 'queued', position, json.dumps(params), utc_now(), group_key),
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


def list_jobs(
    conn: sqlite3.Connection, kind: str | None = None, status: str | None = None, group_key: str | None = None
) -> list[dict]:
    """Trabajos filtrados por tipo, estado y/o grupo de tomas, en orden de posición."""
    clauses, args = [], []
    for column, value in (('kind', kind), ('status', status), ('group_key', group_key)):
        if value is not None:
            clauses.append(f'{column} = ?')
            args.append(value)
    where = f'WHERE {" AND ".join(clauses)}' if clauses else ''
    return [_decode(row) for row in conn.execute(f'SELECT * FROM jobs {where} ORDER BY position', args)]


def star(conn: sqlite3.Connection, job_id: int) -> bool:
    """Marca la toma como la elegida de su grupo y desmarca las demás del grupo (AC-5). False si no existe.
    Una sola sentencia: la conexión está en autocommit, así que el cambio es atómico."""
    job = get(conn, job_id)
    if job is None:
        return False
    if job['group_key'] is None:  # sin grupo no hay con quién compararla: solo ella
        conn.execute('UPDATE jobs SET starred = 1 WHERE id = ?', (job_id,))
    else:
        conn.execute(
            'UPDATE jobs SET starred = CASE WHEN id = ? THEN 1 ELSE 0 END WHERE group_key = ?',
            (job_id, job['group_key']),
        )
    return True
