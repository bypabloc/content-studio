"""Caché de diarizaciones (spec 035, AC-8): el resultado de un audio en `<datos>/diarizations/<sha1>.json`.

Sin tabla: quien la busca es `job_main`, que corre en el Python del server y no recibe la ruta de la base.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from content_studio import paths


def cache_key(source: Path, counts: dict[str, int]) -> str:
    """sha1 de la ruta, el mtime, el tamaño y los hablantes pedidos: cambiar cualquiera es otra entrada."""
    stat = source.stat()
    text = f'{source.resolve()}|{stat.st_mtime}|{stat.st_size}|{json.dumps(counts, sort_keys=True)}'
    return hashlib.sha1(text.encode('utf-8'), usedforsecurity=False).hexdigest()


def json_path(key: str) -> Path:
    """Dónde va el resultado de una diarización: `<datos>/diarizations/<clave>.json`."""
    return paths.data_dir() / 'diarizations' / f'{key}.json'
