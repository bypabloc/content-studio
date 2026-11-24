"""Índice de la biblioteca (spec 020, D-1): rutas y metadatos de las salidas de los trabajos y las carpetas vigiladas.

La base guarda solo rutas, tamaños, fechas y la duración; nunca el contenido. Un trabajo que termina `done` registra
los medios de su carpeta (sin subcarpetas: `blocks/` son piezas internas). Los `done` anteriores a la migración 7 se
indexan una vez con `backfill`.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from content_studio.common import ffmpeg
from content_studio.db import settings
from content_studio.db.connection import utc_now
from content_studio.media.formats import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS

SUBTITLE_EXTENSIONS = frozenset({'.srt', '.vtt', '.ass'})
BACKFILLED = 'library.backfilled'  # setting: el índice inicial de los trabajos anteriores ya corrió
SKIPPED_PREFIXES = ('engine.', 'system.', 'storage.', 'voice.', 'library.')  # mantenimiento: no deja medios del usuario
SKIPPED_KINDS = frozenset({'editor.proxy', 'music.samples', 'transcribe', 'clean.analyze'})


def media_type(path: Path) -> str | None:
    """`audio`, `video`, `subtitle` u `other` (imágenes) por la extensión; None si no es un medio."""
    suffix = path.suffix.lower()
    if suffix in AUDIO_EXTENSIONS:
        return 'audio'
    if suffix in VIDEO_EXTENSIONS:
        return 'video'
    if suffix in SUBTITLE_EXTENSIONS:
        return 'subtitle'
    return 'other' if suffix in IMAGE_EXTENSIONS else None


def item_kind(job_kind: str) -> str | None:
    """El `kind` del ítem: `media.convert` → `convert`, `clean.render` → `clean`; None si no deja salidas."""
    if job_kind in SKIPPED_KINDS or job_kind.startswith(SKIPPED_PREFIXES):
        return None
    head, _, tail = job_kind.partition('.')
    return tail if head == 'media' and tail else head


def probe(path: Path, kind: str) -> dict:
    """Duración (y tamaño de cuadro en video) con ffprobe; None en lo que no se puede leer."""
    found: dict = {'duration': None, 'width': None, 'height': None}
    if kind not in ('audio', 'video'):
        return found
    try:
        found['duration'] = ffmpeg.probe_duration(path)
        if kind == 'video':
            found['width'], found['height'] = ffmpeg.video_size(path)
    except (OSError, subprocess.CalledProcessError, ValueError):
        pass
    return found


def upsert(
    conn: sqlite3.Connection,
    path: Path,
    kind: str,
    origin: str,
    job_id: int | None = None,
    folder_id: int | None = None,
) -> int | None:
    """Agrega o actualiza el ítem de `path` (la ruta es única) y lo marca presente. None si no es un medio."""
    media = media_type(path)
    if media is None or not path.is_file():
        return None
    stat = path.stat()
    meta = probe(path, media)
    conn.execute(
        'INSERT INTO library_items (path, kind, origin, job_id, folder_id, size, mtime, duration, width, height, '
        'media_type, missing, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?) '
        'ON CONFLICT(path) DO UPDATE SET size = excluded.size, mtime = excluded.mtime, duration = excluded.duration, '
        'width = excluded.width, height = excluded.height, missing = 0, indexed_at = excluded.indexed_at',
        (str(path), kind, origin, job_id, folder_id, stat.st_size, stat.st_mtime, meta['duration'], meta['width'],
         meta['height'], media, utc_now()),
    )  # fmt: skip
    return conn.execute('SELECT id FROM library_items WHERE path = ?', (str(path),)).fetchone()[0]


def job_outputs(output_dir: str | None) -> list[Path]:
    """Los medios de la carpeta del trabajo, sin entrar en subcarpetas, en orden de nombre."""
    folder = Path(output_dir or '')
    if not output_dir or not folder.is_dir():
        return []
    return sorted(path for path in folder.iterdir() if path.is_file() and media_type(path) is not None)


def result_output(output_dir: str | None) -> list[Path]:
    """El medio que un trabajo deja fuera de su carpeta y anota en `result.json` (el render del Editor, spec 023)."""
    try:
        output = json.loads((Path(output_dir or '') / 'result.json').read_text(encoding='utf-8')).get('output')
    except (OSError, ValueError, AttributeError):
        return []
    path = Path(output) if output_dir and isinstance(output, str) else None
    return [path] if path is not None and path.is_file() and media_type(path) else []


def register_job(conn: sqlite3.Connection, job: dict) -> list[int]:
    """Registra las salidas de un trabajo terminado y devuelve los ids de sus ítems."""
    kind = item_kind(job['kind'])
    if kind is None:
        return []
    found = [*job_outputs(job['output_dir']), *result_output(job['output_dir'])]
    ids = [upsert(conn, path, kind, 'job', job_id=job['id']) for path in found]
    return [item for item in ids if item is not None]


def backfill(conn: sqlite3.Connection) -> int:
    """Indexa una sola vez los trabajos `done` anteriores a la biblioteca. Devuelve cuántos ítems agregó."""
    if settings.get(conn, BACKFILLED):
        return 0
    added = 0
    for row in conn.execute("SELECT id, kind, output_dir FROM jobs WHERE status = 'done' ORDER BY id").fetchall():
        added += len(register_job(conn, dict(row)))
    settings.set_value(conn, BACKFILLED, True)
    return added
