"""Listener de la red local (spec 032, D-1): un segundo uvicorn en la IP elegida, con TLS y apagado por defecto."""

from __future__ import annotations

import ipaddress
import socket
import threading
import time
from contextlib import closing, suppress
from pathlib import Path
from typing import Any

from content_studio.db import connection, schema, settings
from content_studio.lan import cert
from content_studio.runtime.idle import IdleClock

PREFIX = 'api.lan.'
DEFAULTS: dict[str, Any] = {'enabled': False, 'address': None, 'port': 41831, 'max_upload_mb': 2048, 'keep_awake': True}
HOLD = 'lan'  # la retención del reloj de inactividad (AC-11)
START_TIMEOUT_S = 15


class LanError(Exception):
    """El listener no arrancó: el código del catálogo de errores."""


def read_settings(db: Path) -> dict[str, Any]:
    """Los ajustes `api.lan.*`, con sus valores por defecto."""
    with closing(connection.connect(db)) as conn:
        schema.migrate(conn)
        return {key: settings.get(conn, PREFIX + key, default) for key, default in DEFAULTS.items()}


def write_settings(db: Path, changes: dict[str, Any]) -> dict[str, Any]:
    """Guarda solo las claves conocidas y devuelve los ajustes completos."""
    with closing(connection.connect(db)) as conn:
        schema.migrate(conn)
        for key, value in changes.items():
            if key in DEFAULTS:
                settings.set_value(conn, PREFIX + key, value)
    return read_settings(db)


def valid_address(address: str) -> bool:
    """Una IPv4 privada en la que se puede escuchar: nunca pública ni 0.0.0.0 (D-1).

    >>> [valid_address(a) for a in ('192.168.1.5', '10.0.0.2', '127.0.0.2', '8.8.8.8', '0.0.0.0', 'x', '::1')]
    [True, True, True, False, False, False, False]
    """
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.version == 4 and ip.is_private and not ip.is_unspecified and not ip.is_link_local


def private_addresses() -> list[str]:
    """Las IPv4 privadas de este equipo (sin loopback), para elegir dónde escuchar."""
    found: set[str] = set()
    with suppress(OSError):
        found.update(str(info[4][0]) for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    try:  # la interfaz de la ruta por defecto: connect() en UDP no manda ningún paquete
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(('192.0.2.1', 9))
            found.add(probe.getsockname()[0])
    except OSError:
        pass
    return sorted(address for address in found if valid_address(address) and not address.startswith('127.'))


class LanListener:
    """Arranca, cambia y apaga el listener de la red local según los ajustes guardados."""

    def __init__(self, db: Path, local_app: Any, clock: IdleClock) -> None:
        """La base, la app local (de la que toma el worker, los eventos y el PIN) y el reloj de inactividad."""
        self.db = db
        self.local_app = local_app
        self.clock = clock
        self._server: Any = None
        self._thread: threading.Thread | None = None
        self._url: str | None = None
        self._lock = threading.Lock()

    def status(self) -> dict[str, Any]:
        """Si escucha y en qué URL."""
        return {'running': self._server is not None, 'url': self._url}

    def apply(self) -> dict[str, Any]:
        """Aplica los ajustes: apaga el listener actual y, si está activa, levanta el nuevo. LanError si no arranca."""
        with self._lock:
            self._stop()
            config = read_settings(self.db)
            on = bool(config['enabled'] and config['address'])
            if on and config['keep_awake']:
                self.clock.hold(HOLD)
            else:
                self.clock.release(HOLD)
            if on:
                self._start(str(config['address']), int(config['port']), int(config['max_upload_mb']))
            return self.status()

    def stop(self) -> None:
        """Apaga el listener y suelta la retención."""
        with self._lock:
            self._stop()
            self.clock.release(HOLD)

    def _start(self, address: str, port: int, max_upload_mb: int) -> None:
        import uvicorn

        from content_studio.api.app import create_app
        from content_studio.api.guards import ActivityGuard

        cert_path, key_path = cert.ensure(self.db.parent, address)
        url = f'https://{address}:{port}'
        state = self.local_app.state
        app = create_app(
            self.db,
            state.token,
            services=state.services,
            worker=state.worker,
            broker=state.broker,
            remote=True,
            pairing=state.pairing,
            cert_path=cert_path,
            lan_url=url,
            max_upload_mb=max_upload_mb,
        )
        config = uvicorn.Config(
            ActivityGuard(app, self.clock),
            host=address,
            port=port,
            ssl_certfile=str(cert_path),
            ssl_keyfile=str(key_path),
            log_level='warning',
        )
        server = uvicorn.Server(config)
        sock = socket.socket()
        try:
            sock.bind((address, port))
        except OSError:
            sock.close()
            raise LanError('lan_port_busy') from None
        thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
        thread.start()
        deadline = time.monotonic() + START_TIMEOUT_S
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not server.started:
            server.should_exit = True
            raise LanError('lan_port_busy')
        self._server, self._thread, self._url = server, thread, url

    def _stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
            if self._thread is not None:
                self._thread.join(10)
        self._server, self._thread, self._url = None, None, None
