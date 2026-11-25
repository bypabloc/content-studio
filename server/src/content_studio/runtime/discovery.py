"""Descubrimiento del server compartido (spec 028, D-2 y D-3): api.json y api-token junto a la base."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
import time
from pathlib import Path

INFO = 'api.json'
TOKEN = 'api-token'


def token(folder: Path, rotate: bool = False) -> str:
    """El token de la instalación: se crea una vez (aunque arranquen dos a la vez) y solo cambia con `rotate`."""
    path = folder / TOKEN
    if rotate:
        _write_atomic(path, secrets.token_hex(32))
    elif not path.is_file():
        _create_once(path, secrets.token_hex(32))
    return _read_retry(path).strip()


def write(folder: Path, info: dict) -> None:
    """Publica la dirección del server para que otras apps la encuentren."""
    _write_atomic(folder / INFO, json.dumps(info))


def read(folder: Path) -> dict | None:
    """La dirección publicada, o None si no hay server anotado."""
    try:
        return json.loads((folder / INFO).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def clear(folder: Path) -> None:
    """Borra la dirección publicada al apagarse el server."""
    (folder / INFO).unlink(missing_ok=True)


def _temp_with(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        handle.write(text)
    if os.name == 'posix':
        os.chmod(name, 0o600)
    return Path(name)


def _create_once(path: Path, text: str) -> None:
    tmp = _temp_with(path, text)
    try:
        os.link(tmp, path)
    except FileExistsError:
        pass
    finally:
        tmp.unlink(missing_ok=True)


def _write_atomic(path: Path, text: str) -> None:
    tmp = _temp_with(path, text)
    for attempt in range(20):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.05)


def _read_retry(path: Path) -> str:
    for attempt in range(20):
        try:
            return path.read_text(encoding='utf-8')
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.05)
    return ''
