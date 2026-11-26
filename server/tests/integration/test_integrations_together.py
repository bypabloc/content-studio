"""Spec 033, AC-1: las cuatro puertas del lote 025-032 conviven en un solo server.

En el mismo proceso llegan un trabajo por `POST /jobs` con el token local, otro por el MCP (el puente de `studio mcp`),
un archivo en una carpeta de entrada y otro desde un dispositivo de la red local. Un servicio falso de conversión
escribe el MP3, así la prueba no necesita ffmpeg ni GPU.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import ssl
import sys
import threading
import time
import urllib.request
from contextlib import closing
from pathlib import Path

import uvicorn
from fastapi.testclient import TestClient

from content_studio.api import events
from content_studio.api.app import create_app
from content_studio.cli.serve import pick_free_port
from content_studio.db import connection
from content_studio.db import jobs as store
from content_studio.inbox import scanner
from content_studio.jobs.worker import Worker
from content_studio.lan import cert
from content_studio.lan.server import LanListener, write_settings
from content_studio.mcp_server.bridge import Bridge
from content_studio.runtime import discovery
from content_studio.runtime.idle import IdleClock
from content_studio.services import registry

WRITE_MP3 = (
    'import pathlib, sys; out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); '
    "(out / 'converted.mp3').write_bytes(b'ID3')"
)


class FakeConvert:
    """`media.convert` sin ffmpeg: escribe un MP3 en la carpeta del trabajo."""

    RESOURCE = 'cpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        return []

    @staticmethod
    def build_command(params: dict, output_dir: Path) -> list[str]:
        return [sys.executable, '-c', WRITE_MP3, str(output_dir)]


def _lan_port() -> int:
    with socket.socket() as sock:
        sock.bind(('127.0.0.2', 0))
        return sock.getsockname()[1]


def _https(url: str, context: ssl.SSLContext, token: str = '', body: bytes | None = None, kind: str = 'json') -> dict:
    request = urllib.request.Request(url, data=body, method='POST' if body is not None else 'GET')
    request.add_header('Content-Type', 'application/json' if kind == 'json' else 'application/octet-stream')
    if token:
        request.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        return json.loads(response.read())


def test_ac1_four_doors_one_server(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(home))
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    monkeypatch.setitem(registry.SERVICES, 'media.convert', FakeConvert)
    db = home / 'content-studio.db'
    main = tmp_path / 'checkout'
    main.mkdir()
    source = tmp_path / 'voz.wav'
    source.write_bytes(b'RIFF')
    inbox_folder = tmp_path / 'entrada'
    inbox_folder.mkdir()
    token = discovery.token(home)
    broker = events.Broker()
    worker = Worker(db, main=main, publish=broker.publish)
    app = create_app(db, token, worker=worker, broker=broker)
    clock = IdleClock(minutes=10)
    lan = LanListener(db, app, clock)
    app.state.lan = lan
    port = pick_free_port()
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started and thread.is_alive():
        time.sleep(0.05)
    worker.start()
    stop = threading.Event()
    threading.Thread(target=scanner.run_forever, args=(db, clock, stop), daemon=True).start()
    discovery.write(home, {'url': f'http://127.0.0.1:{port}', 'port': port, 'pid': os.getpid(), 'version': 'test'})
    local = TestClient(app)
    headers = {'Authorization': f'Bearer {token}'}
    try:
        # 1. La API local, con el token de la instalación.
        local_job = local.post(
            '/jobs', json={'kind': 'media.convert', 'params': {'input': str(source), 'target': 'mp3'}}, headers=headers
        ).json()['id']
        # 2. El MCP: el mismo puente que sirve `studio mcp` por stdio, contra el server de api.json.
        called = asyncio.run(
            Bridge(db, poll_s=0.05, main=main).call(
                'studio_convert_media', {'input_path': str(source), 'target': 'mp3'}
            )
        )
        assert not called.is_error, called.text
        mcp_job = called.structured['job_id']
        # 3. Una carpeta de entrada.
        folder = {'path': str(inbox_folder), 'kind': 'media.convert', 'params': {'target': 'mp3'}, 'keep_awake': True}
        assert local.post('/inbox/folders', json=folder, headers=headers).status_code == 201
        (inbox_folder / 'soltado.wav').write_bytes(b'RIFF')
        # 4. Un dispositivo de la red local: activar, emparejar, subir y encolar con su token.
        write_settings(db, {'enabled': True, 'address': '127.0.0.2', 'port': _lan_port()})
        url = lan.apply()['url']
        pinned = ssl.create_default_context(cafile=str(home / cert.CERT_NAME))
        pinned.check_hostname = False
        pin = local.post('/lan/pairing', headers=headers).json()['pin']
        device = _https(f'{url}/pair', pinned, body=json.dumps({'pin': pin, 'name': 'celular'}).encode())['token']
        upload = _https(f'{url}/uploads?name=lan.wav', pinned, device, body=b'RIFF', kind='raw')
        lan_body = json.dumps({'kind': 'media.convert', 'params': {'input': upload['ref'], 'target': 'mp3'}}).encode()
        lan_job = _https(f'{url}/jobs', pinned, device, body=lan_body)['id']

        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            with closing(connection.connect(db)) as conn:
                jobs = store.list_jobs(conn, kind='media.convert')
            if len(jobs) == 4 and all(job['status'] == 'done' for job in jobs):
                break
            time.sleep(0.2)

        assert len(jobs) == 4, jobs
        assert {job['status'] for job in jobs} == {'done'}
        assert {local_job, mcp_job, lan_job} < {job['id'] for job in jobs}
        assert {job['owner_pid'] for job in jobs} == {os.getpid()}  # un solo worker: el de este server
        assert discovery.read(home)['url'] == f'http://127.0.0.1:{port}'
        assert next(job for job in jobs if job['id'] == lan_job)['client_id'] is not None
    finally:
        stop.set()
        lan.stop()
        worker.stop()
        server.should_exit = True
        thread.join(15)
