"""Carpetas vigiladas (spec 020, D-1): se recorren al abrir la Biblioteca y con «Actualizar», sin un watcher.

Agrega los medios nuevos, actualiza los que cambiaron de tamaño o fecha y marca `missing = 1` los que ya no están.
Nunca borra un registro: lo hace el usuario desde la Biblioteca. Una salida ya indexada por su trabajo conserva su
origen. `python -m content_studio.library.scan [--folder ID]` es el comando del trabajo `library.scan`.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from content_studio import paths
from content_studio.db import connection, schema, settings
from content_studio.db.connection import utc_now
from content_studio.library import index

IGNORED = 'library.ignored'  # rutas que el usuario quitó del índice y pidió no volver a agregar
LAST_SCAN = 'library.last_scan'


def add_folder(conn: sqlite3.Connection, path: Path, name: str | None = None) -> int:
    """Registra la carpeta (una vez por ruta) y devuelve su id. ValueError si no es una carpeta."""
    folder = path.expanduser().resolve()
    if not folder.is_dir():
        raise ValueError(f'not a folder: {folder}')
    conn.execute(
        'INSERT INTO library_folders (path, name, added_at) VALUES (?, ?, ?) ON CONFLICT(path) DO NOTHING',
        (str(folder), name or folder.name, utc_now()),
    )
    return conn.execute('SELECT id FROM library_folders WHERE path = ?', (str(folder),)).fetchone()[0]


def list_folders(conn: sqlite3.Connection) -> list[dict]:
    """Las carpetas vigiladas, en el orden en que se agregaron."""
    return [dict(row) for row in conn.execute('SELECT * FROM library_folders ORDER BY id')]


def remove_folder(conn: sqlite3.Connection, folder_id: int) -> bool:
    """Deja de vigilar la carpeta y quita sus ítems del índice; los archivos no se tocan. False si no existe."""
    return conn.execute('DELETE FROM library_folders WHERE id = ?', (folder_id,)).rowcount > 0


def _files(folder: Path, ignored: set[str]) -> dict[str, os.stat_result]:
    """Los medios de la carpeta y sus subcarpetas, por ruta, con su stat."""
    found = {}
    for root, _dirs, names in os.walk(folder):
        for name in names:
            path = Path(root) / name
            if index.media_type(path) is not None and str(path) not in ignored:
                found[str(path)] = path.stat()
    return found


def scan(conn: sqlite3.Connection, folder_id: int | None = None) -> dict[str, int]:
    """Escanea una carpeta o todas; devuelve cuántos ítems se agregaron, actualizaron y quedaron faltantes."""
    ignored = set(settings.get(conn, IGNORED, []) or [])
    counts = {'added': 0, 'updated': 0, 'missing': 0}
    folders = [f for f in list_folders(conn) if folder_id is None or f['id'] == folder_id]
    for folder in folders:
        present = _files(Path(folder['path']), ignored)
        rows = conn.execute('SELECT path, size, mtime, missing, folder_id FROM library_items')
        known = {row['path']: row for row in rows}
        for path, stat in present.items():
            row = known.get(path)
            if row is None:
                index.upsert(conn, Path(path), 'watched', 'watched', folder_id=folder['id'])
                counts['added'] += 1
            elif row['folder_id'] == folder['id'] and (
                row['missing'] or row['size'] != stat.st_size or row['mtime'] != stat.st_mtime
            ):
                index.upsert(conn, Path(path), 'watched', 'watched', folder_id=folder['id'])
                counts['updated'] += 1
        gone = [path for path, row in known.items() if row['folder_id'] == folder['id'] and not row['missing']]
        for path in gone:
            if path not in present:
                conn.execute('UPDATE library_items SET missing = 1 WHERE path = ?', (path,))
                counts['missing'] += 1
    settings.set_value(conn, LAST_SCAN, utc_now())
    return counts


def main(argv: list[str] | None = None) -> int:
    """Entrada del trabajo `library.scan`: escanea la base de `CONTENT_STUDIO_DB` e imprime los conteos en JSON."""
    ap = argparse.ArgumentParser(description='Scan the watched folders of the library.')
    ap.add_argument('--folder', type=int, help='scan only this folder id')
    args = ap.parse_args(argv)
    with closing(connection.connect(paths.db_path())) as conn:
        schema.migrate(conn)
        print(json.dumps(scan(conn, args.folder)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
