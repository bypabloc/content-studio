"""Recibos de las carpetas de entrada (spec 030, D-3): al terminar, el original y sus salidas van a done/, o el error a
failed/, con un recibo JSON al lado. Lo asienta el sondeo, así cubre también los trabajos de la CLI y los de antes de un
reinicio."""

from __future__ import annotations

import json
import shutil
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from content_studio.db import jobs
from content_studio.db.connection import utc_now
from content_studio.inbox import store

FINISHED = ('done', 'error', 'cancelled')
NOT_RESULT = ('params.json',)  # lo que el worker deja en cada carpeta de salida y no es un resultado


def settle(conn: sqlite3.Connection) -> None:
    """Asienta cada archivo tomado cuyo trabajo ya terminó. Un error de disco no corta a los demás: se reintenta."""
    for item in store.processing_items(conn):
        job = jobs.get(conn, item['job_id'])
        if job is None or job['status'] not in FINISHED:
            continue
        root = Path(item['path'])
        try:
            if job['status'] == 'done':
                _done(conn, item, root, job)
            else:
                code = job['error_code'] or job['status']
                message = job['error_detail'] or code
                fail(conn, item['id'], root, item['name'], code=code, message=message, job_id=job['id'])
        except OSError:
            continue


def fail(
    conn: sqlite3.Connection,
    item_id: int,
    root: Path,
    name: str,
    *,
    code: str,
    message: str,
    errors: Sequence[dict] = (),
    job_id: int | None = None,
) -> None:
    """Deja el original en failed/<nombre>/ con su <nombre>.error.json y marca el archivo como fallido."""
    target = root / 'failed' / name
    target.mkdir(parents=True, exist_ok=True)
    source = root / 'processing' / name
    if source.exists():
        shutil.move(str(source), str(target / name))
    _write(target / f'{name}.error.json', {'job_id': job_id, 'code': code, 'message': message, 'errors': list(errors)})
    store.update_item(conn, item_id, state='failed')


def _done(conn: sqlite3.Connection, item: dict[str, Any], root: Path, job: dict[str, Any]) -> None:
    """Deja el original y las salidas en done/<nombre>/, con <nombre>.result.json."""
    name = item['name']
    target = root / 'done' / name
    target.mkdir(parents=True, exist_ok=True)
    outputs = _copy_outputs(job['output_dir'], target)
    source = root / 'processing' / name
    if source.exists():
        shutil.move(str(source), str(target / name))
    finished = job['finished_at'] or utc_now()
    _write(
        target / f'{name}.result.json',
        {'job_id': job['id'], 'kind': job['kind'], 'outputs': outputs, 'finished_at': finished},
    )
    store.update_item(conn, item['id'], state='done')


def _copy_outputs(output_dir: str | None, target: Path) -> list[str]:
    """Copia las salidas del trabajo a `target` y devuelve sus rutas; el original de out/ se queda donde está."""
    if not output_dir or not Path(output_dir).is_dir():
        return []
    copied = []
    for source in sorted(Path(output_dir).iterdir()):
        if source.is_file() and source.name not in NOT_RESULT:
            shutil.copy2(source, target / source.name)
            copied.append(str((target / source.name).resolve()))
    return copied


def _write(path: Path, data: dict[str, Any]) -> None:
    """Escribe un recibo JSON en UTF-8, legible."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
