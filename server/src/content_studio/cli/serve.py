"""`studio serve` (spec 004, D-5 y D-3; spec 028): la API en 127.0.0.1 y el worker de la cola, hasta apagarse."""

from __future__ import annotations

import importlib.metadata
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn

from content_studio.api import events
from content_studio.api.app import create_app
from content_studio.api.guards import ActivityGuard, HostGuard
from content_studio.db import connection, jobs, schema, settings
from content_studio.db.connection import utc_now
from content_studio.inbox import scanner as inbox
from content_studio.jobs.worker import Worker
from content_studio.lan.server import LanError, LanListener
from content_studio.runtime import discovery, idle, instance
from content_studio.system import tools

DEFAULT_PORT = 41830  # spec 028, D-1: IANA sin asignar y fuera de los rangos de Windows de este equipo
DEFAULT_IDLE_MINUTES = 10
IDLE_CHECK_SECONDS = 30


def pick_free_port() -> int:
    """Un puerto libre de 127.0.0.1, el que elige el sistema."""
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def ready_line(port: int, token: str | None = None) -> str:
    """La línea que lee Tauri cuando la API escucha. El token solo va si el server lo generó."""
    ready = {'port': port} | ({'token': token} if token else {})
    return json.dumps({'ready': ready})


def _port_free(port: int) -> bool:
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            return False
    return True


def _configured_port(db: Path) -> int:
    conn = connection.connect(db)
    try:
        schema.migrate(conn)
        value = settings.get(conn, 'api.port')
    finally:
        conn.close()
    return int(str(value)) if value else DEFAULT_PORT


def _chosen_port(db: Path, port: int | None) -> int:
    """El puerto pedido (0 = uno libre); si está ocupado o reservado, otro, anotado en el log (AC-3)."""
    if port == 0:
        return pick_free_port()
    wanted = port if port is not None else _configured_port(db)
    if _port_free(wanted):
        return wanted
    chosen = pick_free_port()
    print(f'port {wanted} is busy or reserved; serving on {chosen}', file=sys.stderr, flush=True)
    return chosen


def _idle_minutes(db: Path) -> float:
    conn = connection.connect(db)
    try:
        schema.migrate(conn)
        value = settings.get(conn, 'api.idle_minutes')
    finally:
        conn.close()
    return float(str(value)) if value else DEFAULT_IDLE_MINUTES


def _busy(db: Path) -> bool:
    conn = connection.connect(db)
    try:
        return any(jobs.list_jobs(conn, status=state) for state in ('queued', 'running'))
    finally:
        conn.close()


def _watch_idle(server: uvicorn.Server, clock: idle.IdleClock, db: Path) -> None:
    """Pide el apagado cuando lleva el límite sin uso y sin trabajos (AC-5)."""
    while not server.should_exit:
        time.sleep(IDLE_CHECK_SECONDS)
        if clock.idle(busy=_busy(db)):
            server.should_exit = True


def _version() -> str:
    try:
        return importlib.metadata.version('content-studio')
    except importlib.metadata.PackageNotFoundError:
        return '0.0.0'


def serve(db: Path, main: Path, port: int | None, token: str | None) -> int:
    """Levanta la API con su worker, anota la dirección y espera hasta que se le pida apagarse."""
    folder = db.parent
    token = token or discovery.token(folder)
    try:
        with instance.hold_lock(folder):
            return _run(db, main, _chosen_port(db, port), token, folder)
    except instance.AlreadyRunning:
        return 3


def _run(db: Path, main: Path, port: int, token: str, folder: Path) -> int:
    broker = events.Broker()
    worker = Worker(db, main=main, publish=broker.publish)
    app = create_app(db, token, worker=worker, broker=broker)
    clock = idle.IdleClock(minutes=_idle_minutes(db))
    guarded = HostGuard(ActivityGuard(app, clock), ['127.0.0.1', 'localhost'])
    server = uvicorn.Server(uvicorn.Config(guarded, host='127.0.0.1', port=port, log_level='warning'))
    app.state.stop = lambda: setattr(server, 'should_exit', True)
    lan = LanListener(db, app, clock)  # spec 032: apagado salvo que se active la red local
    app.state.lan = lan
    tools.detect()
    worker.start()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    threading.Thread(target=_watch_idle, args=(server, clock, db), daemon=True).start()
    inbox_stop = threading.Event()
    threading.Thread(target=inbox.run_forever, args=(db, clock, inbox_stop), daemon=True).start()
    while not server.started and thread.is_alive():
        time.sleep(0.05)
    discovery.write(
        folder,
        {
            'url': f'http://127.0.0.1:{port}',
            'port': port,
            'pid': os.getpid(),
            'version': _version(),
            'started_at': utc_now(),
        },
    )
    print(ready_line(port), flush=True)
    try:
        lan.apply()
    except LanError as error:
        print(f'LAN listener not started ({error}); check api.lan.port in Settings > Integrations', file=sys.stderr)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.should_exit = True
        thread.join(5)
    discovery.clear(folder)
    lan.stop()
    inbox_stop.set()
    worker.stop()
    return 0
