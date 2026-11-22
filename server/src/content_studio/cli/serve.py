"""`studio serve` (spec 004, D-5 y D-3): la API en 127.0.0.1 y el worker de la cola, hasta Ctrl+C."""

from __future__ import annotations

import json
import secrets
import socket
import threading
import time
from pathlib import Path

import uvicorn

from content_studio.api import events
from content_studio.api.app import create_app
from content_studio.jobs.worker import Worker
from content_studio.system import tools


def pick_free_port() -> int:
    """Un puerto libre de 127.0.0.1, el que elige el sistema."""
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def ready_line(port: int, token: str | None = None) -> str:
    """La línea que lee Tauri cuando la API escucha. El token solo va si el server lo generó."""
    ready = {'port': port} | ({'token': token} if token else {})
    return json.dumps({'ready': ready})


def serve(db: Path, main: Path, port: int, token: str | None) -> int:
    """Levanta la API con su worker. Imprime `ready` cuando escucha y espera hasta Ctrl+C."""
    generated = token is None
    token = token or secrets.token_urlsafe(32)
    port = port or pick_free_port()
    broker = events.Broker()
    worker = Worker(db, main=main, publish=broker.publish)
    app = create_app(db, token, worker=worker, broker=broker)
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning'))
    tools.detect()
    worker.start()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started and thread.is_alive():
        time.sleep(0.05)
    print(ready_line(port, token if generated else None), flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.should_exit = True
        thread.join(5)
    worker.stop()
    return 0
