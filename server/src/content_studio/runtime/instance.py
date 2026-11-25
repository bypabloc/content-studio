"""Instancia única y arranque del server compartido (spec 028, D-4): lock de archivo y ensure_running."""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.runtime import discovery

LOCK = 'api.lock'


class AlreadyRunning(RuntimeError):
    """Otro server de esta instalación tiene el lock."""


@contextlib.contextmanager
def hold_lock(folder: Path) -> Iterator[None]:
    """Retiene el lock mientras el server vive; el sistema lo suelta si el proceso muere."""
    folder.mkdir(parents=True, exist_ok=True)
    handle = open(folder / LOCK, 'a+b')  # noqa: SIM115 - el lock vive mientras el handle está abierto
    try:
        _lock(handle)
    except OSError as error:
        handle.close()
        raise AlreadyRunning(str(folder / LOCK)) from error
    try:
        yield
    finally:
        _unlock(handle)
        handle.close()


def _lock(handle: Any) -> None:
    if sys.platform == 'win32':
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(handle: Any) -> None:
    if sys.platform == 'win32':
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def alive(info: dict[str, Any], token: str, timeout: float = 2) -> bool:
    """True si el server anotado responde a /health con el token."""
    request = urllib.request.Request(f'{info["url"]}/health', headers={'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return bool(response.status == 200)
    except (OSError, ValueError):
        return False


def log_path() -> Path:
    """El log del server compartido (spec 028, AC-3)."""
    return paths.logs_dir() / 'server.log'


def ensure_running(db: Path, timeout: float = 30, port: int | None = None) -> dict[str, Any]:
    """La dirección del server de la instalación; lo arranca sin ventana si no hay ninguno vivo."""
    folder = db.parent
    token = discovery.token(folder)
    info = discovery.read(folder)
    if info and alive(info, token):
        return info
    discovery.clear(folder)
    _launch(db, port)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        info = discovery.read(folder)
        if info and alive(info, token):
            return info
        time.sleep(0.2)
    raise TimeoutError(f'the server did not answer in {timeout:g} s; see {log_path()}')


def _launch(db: Path, port: int | None) -> None:
    command = [sys.executable, '-m', 'content_studio.cli.main', '--db', str(db), 'serve']
    if port is not None:
        command += ['--port', str(port)]
    log = log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    detached: dict[str, Any] = (
        {'creationflags': getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NO_WINDOW', 0)}
        if os.name == 'nt'
        else {'start_new_session': True}
    )
    with log.open('ab') as out:
        subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=out, **detached)


def stop(folder: Path, timeout: float = 15) -> bool:
    """Pide el apagado al server anotado y espera a que deje de responder; False si no hay ninguno."""
    info = discovery.read(folder)
    if info is None:
        return False
    token = discovery.token(folder)
    request = urllib.request.Request(
        f'{info["url"]}/server/stop', method='POST', headers={'Authorization': f'Bearer {token}'}
    )
    with contextlib.suppress(OSError, ValueError):
        urllib.request.urlopen(request, timeout=5).close()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and alive(info, token):
        time.sleep(0.2)
    discovery.clear(folder)
    return True
