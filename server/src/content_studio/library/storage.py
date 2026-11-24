"""Espacio de la biblioteca (spec 020, D-5): por tipo, lo más pesado y las tomas no elegidas. Nunca borra nada solo.

Las sumas por tipo salen de los `size` del índice; los totales de la carpeta de salidas y de cada carpeta vigilada se
miden en disco (incluyen lo no indexado). Los motores tienen su propia pantalla y no se cuentan.
"""

from __future__ import annotations

import contextlib
import os
import sqlite3
from pathlib import Path

from content_studio.library import scan

HEAVIEST = 50


def folder_size(folder: Path) -> int:
    """Bytes de los archivos de la carpeta y sus subcarpetas; 0 si no existe."""
    total = 0
    for root, _dirs, names in os.walk(folder):
        for name in names:
            with contextlib.suppress(OSError):
                total += (Path(root) / name).stat().st_size
    return total


def summary(conn: sqlite3.Connection, outputs: Path) -> dict:
    """`by_kind`, `heaviest` (50), `unchosen` y los totales de `outputs` y de cada carpeta vigilada."""
    by_kind = [
        {'kind': kind, 'size': size, 'count': count}
        for kind, size, count in conn.execute(
            'SELECT kind, SUM(size), COUNT(*) FROM library_items WHERE missing = 0 GROUP BY kind ORDER BY 2 DESC'
        )
    ]
    heaviest = [
        dict(row)
        for row in conn.execute(
            'SELECT * FROM library_items WHERE missing = 0 ORDER BY size DESC, id LIMIT ?', (HEAVIEST,)
        )
    ]
    unchosen = [
        dict(row)
        for row in conn.execute(
            'SELECT i.* FROM library_items i JOIN jobs j ON j.id = i.job_id '
            'WHERE i.missing = 0 AND j.starred = 0 AND j.group_key IN '
            '(SELECT group_key FROM jobs WHERE starred = 1 AND group_key IS NOT NULL) ORDER BY i.size DESC, i.id'
        )
    ]
    folders = [{**folder, 'size': folder_size(Path(folder['path']))} for folder in scan.list_folders(conn)]
    return {
        'by_kind': by_kind,
        'heaviest': heaviest,
        'unchosen': unchosen,
        'outputs': {'path': str(outputs), 'size': folder_size(outputs)},
        'folders': folders,
    }
