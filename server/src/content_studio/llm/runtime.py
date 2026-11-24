"""llama-server bajo demanda (spec 021, D-1): un proceso hijo con API compatible con OpenAI.

`ensure_running(model)` arranca `llama-server` con el GGUF del modelo en un puerto libre de 127.0.0.1, espera
`GET /health` y devuelve la URL; `stop()` lo apaga. En Windows el proceso entra en un Job Object que lo mata si el
server muere, así nunca queda un modelo huérfano ocupando la VRAM. Quién lo apaga y cuándo lo decide el worker
(`jobs/llm_warm.py`), que además tiene el turno de la GPU.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import IO, Any

from content_studio import paths
from content_studio.llm import models
from content_studio.llm.client import LlmError

HEALTH_TIMEOUT = 180.0  # cargar 6 GB desde un disco lento
_JOB: Any = None  # el Job Object de Windows, abierto mientras viva el server


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return int(probe.getsockname()[1])


def command(model: str, root: Path, port: int) -> list[str]:
    """El comando de llama-server para un modelo: todo en la GPU, plantilla del modelo (jinja) y sin la web."""
    spec = models.MODELS[model]
    return [
        str(models.server_path(root)),
        '-m',
        str(models.gguf_path(model, root)),
        '-c',
        str(spec.context),
        '-ngl',
        '99',
        '--jinja',
        '--no-webui',
        '--host',
        '127.0.0.1',
        '--port',
        str(port),
    ]


def _launch(arguments: list[str], log: IO[bytes]) -> subprocess.Popen:
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)  # solo existe en Windows
    return subprocess.Popen(
        arguments, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags
    )


def _bind_to_job(process: subprocess.Popen) -> None:
    """Windows: el proceso muere con el server (JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)."""
    if sys.platform != 'win32':
        return
    import ctypes

    global _JOB
    kernel = ctypes.windll.kernel32
    if _JOB is None:

        class Basic(ctypes.Structure):
            _fields_ = [
                ('user_time', ctypes.c_int64),
                ('job_time', ctypes.c_int64),
                ('flags', ctypes.c_uint32),
                ('min_set', ctypes.c_size_t),
                ('max_set', ctypes.c_size_t),
                ('processes', ctypes.c_uint32),
                ('affinity', ctypes.c_size_t),
                ('priority', ctypes.c_uint32),
                ('scheduling', ctypes.c_uint32),
            ]

        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', ctypes.c_uint64 * 6), ('limits', ctypes.c_size_t * 4)]

        job = kernel.CreateJobObjectW(None, None)
        info = Extended()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        kernel.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))  # extended limits
        _JOB = job
    kernel.AssignProcessToJobObject(_JOB, int(process._handle))  # type: ignore[attr-defined]


class Runtime:
    """Un llama-server a la vez: el modelo cargado, su proceso y su URL."""

    def __init__(
        self,
        root: Path | None = None,
        log_path: Path | None = None,
        launch: Callable[[list[str], IO[bytes]], subprocess.Popen] = _launch,
        health_timeout: float = HEALTH_TIMEOUT,
    ) -> None:
        """`root` es la carpeta de motores (por defecto la configurada); el log va a logs/llama-server.log."""
        self.root = root
        self.log_path = log_path or paths.LOGS / 'llama-server.log'
        self.launch = launch
        self.health_timeout = health_timeout
        self.model: str | None = None
        self.process: subprocess.Popen | None = None
        self.url = ''
        self._log: IO[bytes] | None = None

    @property
    def running(self) -> bool:
        """¿Hay un modelo cargado y su proceso sigue vivo?"""
        return self.process is not None and self.process.poll() is None

    def ensure_running(self, model: str) -> str:
        """La URL de un llama-server con `model` cargado; lo arranca (o cambia de modelo) si hace falta."""
        if self.running and self.model == model:
            return self.url
        self.stop()
        root = self.root or paths.engines_dir()
        if model not in models.MODELS or not models.installed(model, root) or not models.server_path(root).is_file():
            raise LlmError('llm_not_installed')
        port = _free_port()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = self.log_path.open('ab')
        self.process = self.launch(command(model, root, port), self._log)
        _bind_to_job(self.process)
        self.url, self.model = f'http://127.0.0.1:{port}', model
        if not self._healthy():
            self.stop()
            raise LlmError('llm_unavailable')
        return self.url

    def _healthy(self) -> bool:
        deadline = time.monotonic() + self.health_timeout
        while time.monotonic() < deadline:
            if not self.running:
                return False
            try:
                with urllib.request.urlopen(self.url + '/health', timeout=2) as response:
                    if response.status == 200:
                        return True
            except (OSError, urllib.error.URLError):  # 503 mientras carga, o el puerto aún cerrado
                pass
            time.sleep(0.25)
        return False

    def stop(self) -> None:
        """Apaga el servidor (si corre) y libera la VRAM. Idempotente."""
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        if self._log is not None:
            self._log.close()
        self.process, self.model, self.url, self._log = None, None, '', None
