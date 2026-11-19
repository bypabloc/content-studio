"""Worker de la cola (spec 004, D-3): una tarea de GPU a la vez con el candado compartido; las de CPU, en paralelo.

Cada hilo abre su propia conexión a la base (SQLite no se comparte entre hilos). Cancelar marca la fila y termina el
árbol de procesos: en Windows con taskkill /T /F, porque terminate() no alcanza a los hijos del motor. Cada cambio de
un trabajo se entrega a `publish` (la API lo manda a /events).
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any

from content_studio import gpu_lock, paths
from content_studio.db import connection, jobs
from content_studio.db.connection import utc_now
from content_studio.jobs import queue, runner
from content_studio.services.registry import SERVICES


def stop_tree(proc: subprocess.Popen) -> None:
    """Termina el proceso y sus hijos. Windows: taskkill /T /F. POSIX: SIGTERM al grupo y SIGKILL si no sale en 5 s."""
    if sys.platform == 'win32':  # mypy solo entiende sys.platform: os.name dejaría killpg sin tipo en Windows
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], capture_output=True, check=False)
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def _status(conn: sqlite3.Connection, job_id: int) -> str | None:
    """Estado actual del trabajo, o None si no existe."""
    row = jobs.get(conn, job_id)
    return row['status'] if row else None


class Worker:
    """Corre los trabajos de la base: GPU de a uno con el candado; CPU en paralelo hasta `cpu_slots`."""

    def __init__(
        self,
        db_path: Path,
        main: Path,
        services: Mapping[str, Any] = SERVICES,
        out_root: Path = paths.OUT,
        log_dir: Path = paths.LOGS / 'jobs',
        cpu_slots: int | None = None,
        poll: float = 0.2,
        publish: Callable[[dict], None] | None = None,
    ) -> None:
        """Worker sobre la base `db_path`; `main` es el checkout principal (dueño del candado de la GPU)."""
        self.db_path = db_path
        self.main = main
        self.services = services
        self.out_root = out_root
        self.log_dir = log_dir
        self.poll = poll
        self._publish = publish or (lambda event: None)
        self._cpu = threading.BoundedSemaphore(cpu_slots or max(1, (os.cpu_count() or 2) // 2))
        self._gpu_busy = False
        self._processes: dict[int, subprocess.Popen] = {}
        self._stop = threading.Event()

    def start(self) -> None:
        """Recupera los `running` de una caída (AC-11) y arranca el despachador en segundo plano."""
        with closing(connection.connect(self.db_path)) as conn:
            queue.recover_interrupted(conn)
        threading.Thread(target=self._dispatch, daemon=True).start()

    def stop(self) -> None:
        """Deja de tomar trabajos nuevos; los que ya corren siguen hasta terminar."""
        self._stop.set()

    def cancel(self, job_id: int) -> bool:
        """Cancela un trabajo en espera o en curso y termina su proceso. True si cambió algo."""
        with closing(connection.connect(self.db_path)) as conn:
            changed = queue.cancel(conn, job_id)
            if changed:
                self._notify(conn, job_id)
        proc = self._processes.get(job_id)
        if proc is not None:
            stop_tree(proc)
        return changed

    def _notify(self, conn: sqlite3.Connection, job_id: int) -> None:
        """Publica el estado actual del trabajo como evento `job` (para /events)."""
        job = jobs.get(conn, job_id)
        if job is not None:
            self._publish({'type': 'job', 'data': job})

    def _dispatch(self) -> None:
        with closing(connection.connect(self.db_path)) as conn:
            while not self._stop.wait(self.poll):
                if queue.paused(conn):
                    continue
                cpu_job = jobs.next_queued(conn, 'cpu')
                if cpu_job and self._cpu.acquire(blocking=False):
                    jobs.update(conn, cpu_job['id'], status='running', started_at=utc_now())
                    self._notify(conn, cpu_job['id'])
                    threading.Thread(target=self._run_cpu, args=(cpu_job,), daemon=True).start()
                    continue
                gpu_job = jobs.next_queued(conn, 'gpu')
                if gpu_job and not self._gpu_busy:
                    self._gpu_busy = True
                    threading.Thread(target=self._run_gpu, args=(gpu_job,), daemon=True).start()

    def _run_cpu(self, job: dict) -> None:
        try:
            with closing(connection.connect(self.db_path)) as conn:
                self._execute(conn, job)
        finally:
            self._cpu.release()

    def _run_gpu(self, job: dict) -> None:
        try:
            with closing(connection.connect(self.db_path)) as conn:
                # Otra sesión puede tener la GPU: se espera sin bloquear las tareas de CPU.
                while not gpu_lock.acquire(self.main, f'{job["kind"]}-{job["id"]}', [job['kind']]):
                    if self._stop.wait(self.poll) or _status(conn, job['id']) != 'queued':
                        return
                try:
                    if _status(conn, job['id']) == 'queued':  # no se canceló mientras esperaba
                        jobs.update(conn, job['id'], status='running', started_at=utc_now())
                        self._notify(conn, job['id'])
                        self._execute(conn, job)
                finally:
                    gpu_lock.release(self.main)
        finally:
            self._gpu_busy = False

    def _execute(self, conn: sqlite3.Connection, job: dict) -> None:
        out_dir = self._output_dir(job)
        jobs.update(conn, job['id'], output_dir=str(out_dir))
        detail = ''
        try:
            command = self.services[job['kind']].build_command(job['params'], out_dir)
            code = runner.run(
                conn,
                job['id'],
                command,
                self.log_dir,
                register=self._register(job['id']),
                on_progress=lambda: self._notify(conn, job['id']),
            )
        except OSError as error:  # el proceso no arrancó (p. ej. falta el venv del motor)
            code, detail = -1, str(error)
        finally:
            self._processes.pop(job['id'], None)
        if _status(conn, job['id']) == 'cancelled':
            return
        if code == 0:
            jobs.update(conn, job['id'], status='done', finished_at=utc_now())
        else:
            jobs.update(
                conn,
                job['id'],
                status='error',
                error_code='process_failed',
                error_detail=detail or f'exit {code}',
                finished_at=utc_now(),
            )
        self._notify(conn, job['id'])

    def _register(self, job_id: int) -> Callable[[subprocess.Popen], None]:
        """Callback para runner.run: guarda el proceso para poder cancelarlo."""
        return lambda proc: self._processes.__setitem__(job_id, proc)

    def _output_dir(self, job: dict) -> Path:
        """out/<tipo>/<AAAA-MM-DD>-<id>-<slug>/ con el params.json del trabajo (spec 004, D-3)."""
        text = str(job['params'].get('text') or job['params'].get('style') or job['kind'])
        slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40] or 'run'
        out_dir = self.out_root / job['kind'] / f'{datetime.now():%Y-%m-%d}-{job["id"]}-{slug}'
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'params.json').write_text(json.dumps(job['params'], ensure_ascii=False, indent=2), encoding='utf-8')
        return out_dir
