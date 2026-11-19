"""Candado del turno de la GPU, compartido por `devtools gpu-turn` y el worker de la cola (spec 004, D-3).

El candado es tmp/gpu-turn/lock.json en el checkout principal (lo ven todos los worktrees) y su formato no cambia:
{pid, platform, work, command, since}. Es solo stdlib, para que devtools lo importe sin el venv del server.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

STILL_ACTIVE = 259


def lock(main: Path) -> Path:
    """Ruta del candado del turno de la GPU, en el checkout principal."""
    return main / 'tmp/gpu-turn/lock.json'


def alive(pid: int, platform: str) -> bool | None:
    """True/False si el proceso vive; None si es de otro sistema (un candado de WSL visto desde Windows)."""
    if platform != sys.platform:
        return None
    if os.name == 'nt':
        import ctypes

        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return code.value == STILL_ACTIVE
    try:
        os.kill(pid, 0)  # señal 0: solo comprueba (en Windows os.kill mataría el proceso)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read(main: Path) -> dict | None:
    """Dueño del turno, o None si está libre (sin candado o con el proceso muerto)."""
    try:
        owner = json.loads(lock(main).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if alive(owner.get('pid', 0), owner.get('platform', '')) is False:
        return None
    return owner


def take(main: Path, job: str, command: list[str]) -> dict | None:
    """Toma el turno (creación atómica); devuelve el dueño actual si está ocupado, o None si lo tomó."""
    lock_file = lock(main)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    owner = read(main)
    if owner:
        return owner
    lock_file.unlink(missing_ok=True)  # candado huérfano: su proceso murió
    data = {'pid': os.getpid(), 'platform': sys.platform, 'work': job, 'command': ' '.join(command)}
    data['since'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    try:
        with lock_file.open('x', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except FileExistsError:
        return read(main) or {'work': '?', 'command': 'another process took the turn at the same time'}
    return None


def release(main: Path) -> None:
    """Suelta el turno si lo tiene esta sesión."""
    lock_file = lock(main)
    try:
        if json.loads(lock_file.read_text(encoding='utf-8')).get('pid') == os.getpid():
            lock_file.unlink()
    except (OSError, ValueError):
        return


def acquire(main: Path, job: str, command: list[str], wait: bool = False, poll: float = 5.0) -> bool:
    """True si toma el turno. Con `wait`, reintenta cada `poll` segundos hasta que otra sesión lo suelte."""
    while take(main, job, command) is not None:
        if not wait:
            return False
        time.sleep(poll)
    return True
