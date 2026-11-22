"""Worker de la cola (spec 004, D-3): una tarea de GPU a la vez con el candado compartido; las de CPU, en paralelo.

Cada hilo abre su propia conexión a la base (SQLite no se comparte entre hilos). Un trabajo se toma con `queue.claim`,
así la CLI y el server no lo corren dos veces. Cancelar, desde este worker o desde otro proceso, termina el árbol de
procesos: en Windows con taskkill /T /F, porque terminate() no alcanza a los hijos del motor. Cada cambio de un trabajo
se entrega a `publish` (la API lo manda a /events).
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
import time
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
from content_studio.services.storage_move import KIND as STORAGE_MOVE

WATCH_SECONDS = 0.5  # cada cuánto mira la base si el trabajo que corre se canceló desde otro proceso


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


def _label(job: dict) -> str:
    """Nombre del trabajo en el candado de la GPU (lo ven `gpu-turn status` y las otras sesiones)."""
    return f'{job["kind"]}-{job["id"]}'


class Worker:
    """Corre los trabajos de la base: GPU de a uno con el candado; CPU en paralelo hasta `cpu_slots`."""

    def __init__(
        self,
        db_path: Path,
        main: Path,
        services: Mapping[str, Any] = SERVICES,
        out_root: Path | None = None,
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
        if changed and proc is not None:
            stop_tree(proc)
        return changed

    def run_now(self, job_id: int) -> str | None:
        """Corre un trabajo en este proceso, espera a que termine y devuelve su estado final (lo usa `studio`)."""
        with closing(connection.connect(self.db_path)) as conn:
            job = jobs.get(conn, job_id)
            if job is None:
                raise ValueError(f'job {job_id} does not exist')
            if job['resource'] == 'gpu':
                while not gpu_lock.acquire(self.main, _label(job), [job['kind']]):
                    time.sleep(self.poll)  # otra sesión tiene la GPU: se espera
                try:
                    self._claim_and_run(conn, job)
                finally:
                    gpu_lock.release(self.main)
            else:
                self._claim_and_run(conn, job)
            return _status(conn, job_id)

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
                    if queue.claim(conn, cpu_job['id']):
                        self._notify(conn, cpu_job['id'])
                        threading.Thread(target=self._run_cpu, args=(cpu_job,), daemon=True).start()
                        continue
                    self._cpu.release()
                if cpu_job and cpu_job['kind'] == STORAGE_MOVE:
                    continue  # Deja terminar los trabajos activos antes de abrir otros.
                gpu_job = jobs.next_queued(conn, 'gpu')
                if gpu_job and not self._gpu_busy:
                    self._gpu_busy = True
                    threading.Thread(target=self._run_gpu, args=(gpu_job,), daemon=True).start()

    def _claim_and_run(self, conn: sqlite3.Connection, job: dict) -> None:
        if queue.claim(conn, job['id']):
            self._notify(conn, job['id'])
            self._execute(conn, job)

    def _run_cpu(self, job: dict) -> None:
        try:
            with closing(connection.connect(self.db_path)) as conn:
                self._execute(conn, job)  # el despachador ya lo tomó: está en running
        finally:
            self._cpu.release()

    def _run_gpu(self, job: dict) -> None:
        try:
            with closing(connection.connect(self.db_path)) as conn:
                # Otra sesión puede tener la GPU: se espera sin bloquear las tareas de CPU.
                while not gpu_lock.acquire(self.main, _label(job), [job['kind']]):
                    if self._stop.wait(self.poll) or _status(conn, job['id']) != 'queued':
                        return
                try:
                    self._claim_and_run(conn, job)
                finally:
                    gpu_lock.release(self.main)
        finally:
            self._gpu_busy = False

    def _execute(self, conn: sqlite3.Connection, job: dict) -> None:
        out_dir = self._output_dir(job)
        jobs.update(conn, job['id'], output_dir=str(out_dir))
        finished = threading.Event()
        threading.Thread(target=self._watch_cancel, args=(job['id'], finished), daemon=True).start()
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
            finished.set()
            self._processes.pop(job['id'], None)
        if _status(conn, job['id']) == 'cancelled':
            return
        if code == 0:
            jobs.update(conn, job['id'], status='done', finished_at=utc_now())
            self._chain(conn, job, out_dir)
        else:
            errors = getattr(self.services[job['kind']], 'ERROR_CODES', {})
            jobs.update(
                conn,
                job['id'],
                status='error',
                error_code=errors.get(code, 'process_failed'),
                error_detail=detail or f'exit {code}',
                finished_at=utc_now(),
            )
        self._notify(conn, job['id'])

    def _chain(self, conn: sqlite3.Connection, job: dict, out_dir: Path) -> None:
        """«Aplicar todos sin revisar» (spec 013, D-4): un análisis con `auto_render` encola su render al terminar."""
        if job['kind'] != 'clean.analyze' or not job['params'].get('auto_render'):
            return
        new_id = queue.enqueue(
            conn, 'clean.render', {'input': job['params']['input'], 'analysis': str(out_dir)}, self.services
        )
        self._notify(conn, new_id)

    def _watch_cancel(self, job_id: int, finished: threading.Event) -> None:
        """Mientras el proceso corre, mira la base: si el trabajo se canceló desde otro proceso, lo termina."""
        with closing(connection.connect(self.db_path)) as conn:
            while not finished.wait(WATCH_SECONDS):
                proc = self._processes.get(job_id)
                if proc is not None and _status(conn, job_id) == 'cancelled':
                    stop_tree(proc)
                    return

    def _register(self, job_id: int) -> Callable[[subprocess.Popen], None]:
        """Callback para runner.run: guarda el proceso para poder cancelarlo."""
        return lambda proc: self._processes.__setitem__(job_id, proc)

    def _output_dir(self, job: dict) -> Path:
        """out/<tipo>/<AAAA-MM-DD>-<id>-<slug>/ con el params.json del trabajo (spec 004, D-3)."""
        text = str(job['params'].get('text') or job['params'].get('style') or job['kind'])
        slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40] or 'run'
        folder = job['kind'].split('.')[0]  # narration.regenerate sale en out/narration/, junto a sus tomas
        out_root = self.out_root if self.out_root is not None else paths.outputs_dir(self.db_path)
        out_dir = out_root / folder / f'{datetime.now():%Y-%m-%d}-{job["id"]}-{slug}'
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'params.json').write_text(json.dumps(job['params'], ensure_ascii=False, indent=2), encoding='utf-8')
        return out_dir
