"""Spec 030, fase 1: no reprocesar al reiniciar (AC-7) y retener el server con keep_awake (AC-8)."""

import json
from pathlib import Path

import pytest

from content_studio.db import connection, schema
from content_studio.inbox import scanner, store
from content_studio.runtime import idle


class FakeConvert:
    """Tipo de trabajo falso: siempre válido, corre en la CPU."""

    RESOURCE = 'cpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        """Sin errores."""
        return []


class FakeTime:
    """Reloj a mano para el IdleClock de la prueba."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / 'content-studio.db'
    conn = connection.connect(path)
    schema.migrate(conn)
    conn.close()
    return path


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    path = tmp_path / 'entrada'
    path.mkdir()
    return path


def test_ac7_does_not_reprocess_after_a_restart(db_path, folder):
    services = {'media.convert': FakeConvert}
    conn = connection.connect(db_path)
    folder_id = store.register(conn, str(folder), 'media.convert', {'target': 'mp3'}, services=services)
    old = folder / 'viejo.wav'
    old.write_bytes(b'RIFF')
    stat = old.stat()
    store.add_item(conn, folder_id, 'viejo.wav', size=stat.st_size, mtime=stat.st_mtime, state='done')
    conn.close()
    (folder / 'nuevo.wav').write_bytes(b'RIFF')  # soltado con el server apagado

    conn = connection.connect(db_path)  # el server arranca de nuevo
    scanner.scan_once(conn, services=services)
    scanner.scan_once(conn, services=services)

    queued = [json.loads(row[0])['input'] for row in conn.execute('SELECT params FROM jobs ORDER BY id')]
    assert queued == [str((folder / 'processing' / 'nuevo.wav').resolve())]
    conn.close()


def test_ac8_keep_awake_holds_the_server_until_released(db_path, folder):
    services = {'media.convert': FakeConvert}
    conn = connection.connect(db_path)
    folder_id = store.register(conn, str(folder), 'media.convert', {'target': 'mp3'}, services=services)
    timer = FakeTime()
    clock = idle.IdleClock(minutes=1, clock=timer)
    scanner.scan_once(conn, services=services, clock=clock)

    timer.now = 600.0  # diez minutos sin uso
    assert clock.idle() is False  # la carpeta con keep_awake mantiene el server

    store.set_keep_awake(conn, folder_id, False)
    scanner.scan_once(conn, services=services, clock=clock)
    timer.now = 1200.0
    assert clock.idle() is True  # sin keep_awake, el server puede apagarse
    conn.close()
