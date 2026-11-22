"""Compilar el binario del worktree, abrirlo dentro de un Job y esperar su CDP (spec 024, D-2, D-5 y D-8).

El Job Object de Windows (`KILL_ON_JOB_CLOSE`) es el cierre: al cerrar su handle, en `finally` o porque devtools
murió, Windows termina la app, WebView2, uv y el server de esa corrida, y nada más. El proceso nace suspendido y se
reanuda ya dentro del Job, así sus hijos también quedan adentro (lo mismo hace `server.rs` con el server).
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
import urllib.request
from collections.abc import Callable
from pathlib import Path

# La primera compilación tarda minutos; esto es solo lo que tarda la ventana en exponer CDP una vez abierta.
CDP_DEADLINE = 60.0
# WebView2 no avisa cuando su CDP escucha: se reintenta con una pausa corta hasta el plazo o hasta que la app muera.
RETRY = 0.25
CREATE_SUSPENDED = 0x00000004
KILL_ON_JOB_CLOSE = 0x00002000
EXTENDED_LIMIT_INFORMATION = 9
STILL_ACTIVE = 259


def build(root: Path, env: dict[str, str], log: Path) -> int:
    """`tauri build --debug --no-bundle` con el target de la corrida; la salida va al log. Devuelve el exit code."""
    log.parent.mkdir(parents=True, exist_ok=True)
    command = ['bun', 'run', '--cwd', 'client', 'tauri', 'build', '--debug', '--no-bundle']
    with log.open('a', encoding='utf-8') as out:
        merged = {**os.environ, **env}
        return subprocess.run(command, cwd=root, env=merged, stdout=out, stderr=subprocess.STDOUT).returncode


def binary(env: dict[str, str]) -> Path:
    """El ejecutable que deja `build` en el target de la corrida."""
    name = 'content-studio.exe' if os.name == 'nt' else 'content-studio'
    return Path(env['CARGO_TARGET_DIR']) / 'debug' / name


def wait_for(
    predicate: Callable[[], bool],
    deadline: float,
    clock: Callable[[], float] = time.monotonic,
    pause: Callable[[float], None] = time.sleep,
) -> bool:
    """True en cuanto `predicate()` lo es; False si vence el plazo."""
    end = clock() + deadline
    while True:
        if predicate():
            return True
        if clock() >= end:
            return False
        pause(RETRY)


def wait_cdp(
    port: int,
    deadline: float = CDP_DEADLINE,
    clock: Callable[[], float] = time.monotonic,
    pause: Callable[[float], None] = time.sleep,
    opener: Callable[..., object] = urllib.request.urlopen,
    alive: Callable[[], bool] = lambda: True,
) -> bool:
    """True cuando `/json/version` responde 200; False si vence el plazo o la app murió antes."""
    url = f'http://127.0.0.1:{port}/json/version'
    end = clock() + deadline

    def answers() -> bool:
        try:
            with opener(url, timeout=2) as response:  # type: ignore[attr-defined]
                return response.status == 200
        except OSError:
            return False

    while alive():
        if answers():
            return True
        if clock() >= end:
            return False
        pause(RETRY)
    return False


def scenarios(root: Path, port: int, run_dir: Path, data: str, names: list[str], log: Path) -> int:
    """Corre los escenarios `tests/e2e/app-check/<nombre>.check.ts` contra el CDP de la corrida."""
    files = [f'app-check/{name}.check.ts' for name in names]
    command = ['bun', 'run', '--cwd', 'tests/e2e', 'playwright', 'test', '-c', 'playwright.app-check.config.ts', *files]
    env = {
        **os.environ,
        'APP_CHECK_CDP': f'http://127.0.0.1:{port}',
        'APP_CHECK_RUN': str(run_dir),
        'APP_CHECK_DATA': data,
    }
    with log.open('a', encoding='utf-8') as out:
        return subprocess.run(command, cwd=root, env=env, stdout=out, stderr=subprocess.STDOUT).returncode


def process_alive(pid: int) -> bool:
    """Si el proceso sigue vivo (para comprobar el cierre del Job)."""
    if sys.platform != 'win32':
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    try:
        kernel32.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code))
        return code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


class _Basic(ctypes.Structure):
    _fields_ = [
        ('PerProcessUserTimeLimit', ctypes.c_int64),
        ('PerJobUserTimeLimit', ctypes.c_int64),
        ('LimitFlags', ctypes.c_uint32),
        ('MinimumWorkingSetSize', ctypes.c_size_t),
        ('MaximumWorkingSetSize', ctypes.c_size_t),
        ('ActiveProcessLimit', ctypes.c_uint32),
        ('Affinity', ctypes.c_size_t),
        ('PriorityClass', ctypes.c_uint32),
        ('SchedulingClass', ctypes.c_uint32),
    ]


class _Extended(ctypes.Structure):
    _fields_ = [
        ('BasicLimitInformation', _Basic),
        ('IoInfo', ctypes.c_uint64 * 6),
        ('ProcessMemoryLimit', ctypes.c_size_t),
        ('JobMemoryLimit', ctypes.c_size_t),
        ('PeakProcessMemoryUsed', ctypes.c_size_t),
        ('PeakJobMemoryUsed', ctypes.c_size_t),
    ]


class Job:
    """Un Job Object con `KILL_ON_JOB_CLOSE` como context manager: al salir mueren todos sus procesos."""

    def __enter__(self) -> Job:
        """Crea el Job."""
        self.handle = self._open()
        return self

    def __exit__(self, *exc: object) -> None:
        """Cierra el Job: Windows termina todos sus procesos."""
        self._close()

    def _open(self) -> object:
        if sys.platform != 'win32':
            raise OSError('Job Objects need Windows')
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.CreateJobObjectW.restype = ctypes.c_void_p
        handle = kernel32.CreateJobObjectW(None, None)
        info = _Extended()
        info.BasicLimitInformation.LimitFlags = KILL_ON_JOB_CLOSE
        size = ctypes.sizeof(info)
        if not handle or not kernel32.SetInformationJobObject(
            ctypes.c_void_p(handle), EXTENDED_LIMIT_INFORMATION, ctypes.byref(info), size
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def _close(self) -> None:
        if sys.platform == 'win32':
            ctypes.WinDLL('kernel32').CloseHandle(ctypes.c_void_p(self.handle))  # type: ignore[arg-type]

    def start(self, command: list[str], env: dict[str, str], log: Path) -> subprocess.Popen[bytes]:
        """Abre `command` suspendido, lo mete en el Job y lo reanuda; su salida va al log."""
        if sys.platform != 'win32':
            raise OSError('Job Objects need Windows')
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('ab') as out:
            proc = subprocess.Popen(
                command, env=env, stdout=out, stderr=subprocess.STDOUT, creationflags=CREATE_SUSPENDED
            )
        process = ctypes.c_void_p(int(proc._handle))  # type: ignore[attr-defined]
        if not ctypes.WinDLL('kernel32').AssignProcessToJobObject(ctypes.c_void_p(self.handle), process):  # type: ignore[arg-type]
            proc.kill()
            raise ctypes.WinError()
        # cspell:ignore ntdll
        ctypes.WinDLL('ntdll').NtResumeProcess(process)
        return proc
