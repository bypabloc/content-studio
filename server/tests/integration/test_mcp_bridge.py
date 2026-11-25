"""Spec 029, fase 1: el puente contra un server de verdad (AC-2, AC-3, AC-5, AC-6 y AC-7).

El server corre en este proceso, con su worker y sus servicios; los servicios falsos escriben archivos o esperan,
así la prueba no necesita motores ni GPU.
"""

import asyncio
import os
import sys
import threading
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import anyio
import pytest
import uvicorn
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams
from mcp.types import ResourceLink, TextContent

from content_studio import gpu_lock
from content_studio.api import events
from content_studio.api.app import create_app
from content_studio.cli.serve import pick_free_port
from content_studio.jobs.worker import Worker
from content_studio.mcp_server import sdk
from content_studio.mcp_server.bridge import Bridge
from content_studio.runtime import discovery, instance
from content_studio.services import registry

EXPECTED_TOOLS = (
    'studio_capabilities',
    'studio_narrate',
    'studio_make_music',
    'studio_transcribe',
    'studio_clean_silences',
    'studio_convert_media',
    'studio_submit_job',
    'studio_get_job',
    'studio_wait_job',
    'studio_cancel_job',
)
ADMIN_WORDS = ('engine', 'storage', 'setting', 'fs', 'trash', 'install', 'uninstall', 'delete', 'remove')

WRITE_WAV = (
    'import pathlib, sys, time; out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); '
    "time.sleep(float(sys.argv[2])); (out / 'narracion.wav').write_bytes(b'RIFF')"
)
SLEEP_WITH_PID = (
    'import os, pathlib, sys, time; pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(120)'
)


class FakeNarration:
    """El servicio de narración, con un proceso que escribe un .wav y no toca motores (AC-3)."""

    RESOURCE = 'cpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        return []

    @staticmethod
    def build_command(params: dict, output_dir: Path) -> list[str]:
        return [sys.executable, '-c', WRITE_WAV, str(output_dir), '0.2']


class FakeSlow:
    """Un trabajo de CPU que tarda un segundo (AC-5)."""

    RESOURCE = 'cpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        return []

    @staticmethod
    def build_command(params: dict, output_dir: Path) -> list[str]:
        return [sys.executable, '-c', WRITE_WAV, str(output_dir), '1.0']


class FakeSleep:
    """Un proceso que anota su pid y espera: lo que AC-6 necesita ver morir."""

    RESOURCE = 'cpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        return []

    @staticmethod
    def build_command(params: dict, output_dir: Path) -> list[str]:
        return [sys.executable, '-c', SLEEP_WITH_PID, params['pid_file']]


class FakeGpu:
    """Un trabajo de GPU: se queda en cola mientras otra sesión tiene el candado (AC-7)."""

    RESOURCE = 'gpu'

    @staticmethod
    def validate(params: dict) -> list[dict]:
        return []

    @staticmethod
    def build_command(params: dict, output_dir: Path) -> list[str]:
        return [sys.executable, '-c', WRITE_WAV, str(output_dir), '0.1']


@asynccontextmanager
async def _client(bridge: Bridge) -> AsyncIterator[ClientSession]:
    """Un cliente MCP conectado en memoria al servidor de `sdk.build_server`: el protocolo real, sin stdio."""
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        server = sdk.build_server(bridge)
        async with anyio.create_task_group() as group:
            group.start_soon(server.run, *server_streams, server.create_initialization_options())
            async with ClientSession(*client_streams) as session:
                await session.initialize()
                yield session
            group.cancel_scope.cancel()


@pytest.fixture
def live(tmp_path, monkeypatch) -> Iterator[tuple[Bridge, Path]]:
    """Un server con su worker en este proceso, en una instalación aislada; devuelve el puente y el checkout."""
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(home))
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    db = home / 'content-studio.db'
    main = tmp_path / 'checkout'
    main.mkdir()
    token = discovery.token(home)
    broker = events.Broker()
    worker = Worker(db, main=main, publish=broker.publish)
    app = create_app(db, token, worker=worker, broker=broker)
    port = pick_free_port()
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 20
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    worker.start()
    discovery.write(home, {'url': f'http://127.0.0.1:{port}', 'port': port, 'pid': os.getpid(), 'version': 'test'})
    try:
        yield Bridge(db, poll_s=0.05, main=main), main
    finally:
        worker.stop()
        server.should_exit = True
        thread.join(15)


def _wait_until(predicate: Any, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return False


def test_ac1_protocol_lists_ten_tools(tmp_path):
    async def list_tools_call():
        async with _client(Bridge(tmp_path / 'content-studio.db', main=tmp_path)) as session:
            return await session.list_tools()

    listed = asyncio.run(list_tools_call())
    assert [tool.name for tool in listed.tools] == list(EXPECTED_TOOLS)
    for tool in listed.tools:
        assert tool.input_schema['type'] == 'object'
        assert tool.output_schema['type'] == 'object'
        assert not any(word in tool.name for word in ADMIN_WORDS)


def test_ac2_first_call_starts_the_server(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(home))
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    db = home / 'content-studio.db'
    try:
        assert discovery.read(home) is None  # no hay server: la primera llamada lo arranca
        result = asyncio.run(Bridge(db, main=tmp_path).call('studio_capabilities', {}))
        assert not result.is_error, result.text
        assert 'job_kinds' in result.structured
        assert (home / 'api.json').is_file()
    finally:
        instance.stop(home)


def test_ac3_narrate_and_wait_return_paths_over_protocol(live, monkeypatch):
    bridge, _ = live
    monkeypatch.setitem(registry.SERVICES, 'narration', FakeNarration)

    async def narrate_and_wait():
        async with _client(bridge) as session:
            started = await session.call_tool('studio_narrate', {'text': 'Hola mundo'})
            job_id = started.structured_content['job_id']
            return await session.call_tool('studio_wait_job', {'job_id': job_id, 'timeout_s': 60})

    done = asyncio.run(narrate_and_wait())
    assert not done.is_error
    assert done.structured_content['status'] == 'done'
    assert all(isinstance(item, (TextContent, ResourceLink)) for item in done.content)  # sin base64 (D-4)
    links = [item for item in done.content if isinstance(item, ResourceLink)]
    assert links and all(str(link.uri).startswith('file:///') for link in links)
    outputs = [item['path'] for item in done.structured_content['outputs']]
    assert outputs and all(Path(path).is_file() for path in outputs)


def test_ac5_wait_reports_progress_and_times_out_without_error(live, monkeypatch):
    bridge, _ = live
    monkeypatch.setitem(registry.SERVICES, 'fake.slow', FakeSlow)

    async def wait_with_progress():
        seen: list[float] = []

        async def on_progress(progress: float, total: float | None, message: str | None) -> None:
            seen.append(progress)

        async with _client(bridge) as session:
            started = await session.call_tool('studio_submit_job', {'kind': 'fake.slow', 'params': {}})
            done = await session.call_tool(
                'studio_wait_job',
                {'job_id': started.structured_content['job_id'], 'timeout_s': 60},
                progress_callback=on_progress,
            )
            slow = await session.call_tool('studio_submit_job', {'kind': 'fake.slow', 'params': {}})
            job_id = slow.structured_content['job_id']
            expired = await session.call_tool('studio_wait_job', {'job_id': job_id, 'timeout_s': 0})
            # El trabajo sigue corriendo tras vencer la espera: se cancela aquí, dentro de la prueba (si no, el
            # worker lo arranca cuando el registro ya no tiene `fake.slow`).
            await session.call_tool('studio_cancel_job', {'job_id': job_id})
            return seen, done, expired

    seen, done, expired = asyncio.run(wait_with_progress())
    assert done.structured_content['status'] == 'done'
    assert seen and seen == sorted(seen)
    assert not expired.is_error
    assert expired.structured_content['timed_out'] is True


def test_ac6_cancel_ends_the_process(live, monkeypatch, tmp_path):
    bridge, _ = live
    monkeypatch.setitem(registry.SERVICES, 'fake.sleep', FakeSleep)
    pid_file = tmp_path / 'pid.txt'
    started = asyncio.run(
        bridge.call('studio_submit_job', {'kind': 'fake.sleep', 'params': {'pid_file': str(pid_file)}})
    )
    assert _wait_until(pid_file.exists, 30), 'el proceso del trabajo nunca arrancó'
    pid = int(pid_file.read_text(encoding='utf-8'))

    cancelled = asyncio.run(bridge.call('studio_cancel_job', {'job_id': started.structured['job_id']}))
    assert cancelled.structured['status'] == 'cancelled'
    assert _wait_until(lambda: not gpu_lock.alive(pid, sys.platform), 15), 'el proceso sigue vivo tras cancelar'


def test_ac7_gpu_queued_says_who_holds_it(live, monkeypatch):
    bridge, main = live
    monkeypatch.setitem(registry.SERVICES, 'fake.gpu', FakeGpu)
    assert gpu_lock.take(main, 'otra-sesion', ['studio']) is None  # otra sesión toma la GPU (formato real)
    started = asyncio.run(bridge.call('studio_submit_job', {'kind': 'fake.gpu', 'params': {}}))
    job_id = started.structured['job_id']
    try:
        assert _wait_until(
            lambda: (
                asyncio.run(bridge.call('studio_get_job', {'job_id': job_id})).structured['job']['status']
                == 'waiting_gpu'
            ),
            20,
        )
        view = asyncio.run(bridge.call('studio_get_job', {'job_id': job_id})).structured['job']
        assert view['waiting_on'].endswith('otra-sesion')
    finally:
        gpu_lock.release(main)  # el candado es de este proceso: se suelta y el worker lo toma
        asyncio.run(bridge.call('studio_cancel_job', {'job_id': job_id}))
