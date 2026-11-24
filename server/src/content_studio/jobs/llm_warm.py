"""El LLM caliente en el worker (spec 021, D-2): nunca dos modelos en la GPU.

Un trabajo `llm.*` recibe la URL de llama-server en `params['llm_url']`. Antes de cualquier otro trabajo de GPU el
servidor se apaga. Después de un `llm.*`, el worker conserva el turno de la GPU y el servidor caliente hasta
`llm.idle_seconds` (2 min por defecto) o hasta que llega un trabajo de GPU distinto, lo que pase primero; los `llm.*`
que llegan mientras tanto corren sin volver a cargar el modelo.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from collections.abc import Callable

from content_studio.db import jobs, settings
from content_studio.jobs import queue
from content_studio.llm import models
from content_studio.llm.runtime import Runtime

PREFIX = 'llm.'
IDLE_SECONDS = 120.0


def is_llm(kind: str) -> bool:
    """¿Es una tarea del asistente?"""
    return kind.startswith(PREFIX)


class LlmWarm:
    """El servidor del asistente que el worker mantiene entre trabajos `llm.*` seguidos."""

    def __init__(self, runtime: Runtime | None = None) -> None:
        """`runtime` se reemplaza en las pruebas por uno simulado."""
        self.runtime = runtime or Runtime()

    @property
    def running(self) -> bool:
        """¿Hay un modelo cargado?"""
        return self.runtime.running

    def prepare(self, conn: sqlite3.Connection, job: dict) -> dict:
        """Los params del trabajo: un `llm.*` recibe `llm_url`; otro trabajo de GPU apaga antes el LLM."""
        if not is_llm(job['kind']):
            if job.get('resource') == 'gpu':
                self.stop()
            return job['params']
        model = job['params'].get('model') or models.selected(conn)
        return {**job['params'], 'llm_url': self.runtime.ensure_running(model), 'llm_model': model}

    def hold(
        self, conn: sqlite3.Connection, run_next: Callable[[dict], None], stop: threading.Event, poll: float
    ) -> None:
        """Mantiene el servidor (y el turno del llamador) hasta el tiempo de espera o un trabajo de GPU distinto."""
        idle = float(settings.get(conn, 'llm.idle_seconds', IDLE_SECONDS))  # type: ignore[arg-type]
        deadline = time.monotonic() + idle
        while self.running and not stop.is_set():
            waiting = None if queue.paused(conn) else jobs.next_queued(conn, 'gpu')
            if waiting is not None:
                if not is_llm(waiting['kind']):
                    break
                run_next(waiting)
                deadline = time.monotonic() + idle
                continue
            if time.monotonic() >= deadline:
                break
            stop.wait(poll)
        self.stop()

    def stop(self) -> None:
        """Apaga el servidor si corre."""
        self.runtime.stop()
