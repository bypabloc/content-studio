"""Eventos en vivo (spec 004, D-4, AC-5): el progreso que imprime un proceso llega a la base y a los suscriptores."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

from content_studio.api.events import Broker, encode, frames
from content_studio.db import connection, jobs, schema
from content_studio.jobs import queue
from content_studio.jobs.worker import Worker

PRINT_PROGRESS = 'print(\'@@progress {"p": 0.5, "stage": "x"}\', flush=True)'


def _next_event(box, wanted: Callable[[dict], bool], timeout: float = 20.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        event = box.get(timeout=1.0)
        if wanted(event):
            return event
    raise AssertionError('no llegó el evento esperado')


def test_encode_writes_the_event_and_the_data_lines():
    assert encode({'type': 'job', 'data': {'progress': 0.5}}) == 'event: job\ndata: {"progress": 0.5}\n\n'


def test_a_subscriber_gets_what_is_published_after_subscribing():
    broker = Broker()
    box = broker.subscribe()

    broker.publish({'type': 'queue', 'data': {'paused': True}})

    assert box.get(timeout=1) == {'type': 'queue', 'data': {'paused': True}}


def test_frames_streams_the_next_event_and_pings_when_idle():
    broker = Broker()
    box = broker.subscribe()
    stream = frames(box, broker)
    assert next(stream) == ': ping\n\n'  # sin eventos: un comentario mantiene viva la conexión

    broker.publish({'type': 'job', 'data': {'id': 1}})

    assert next(stream) == 'event: job\ndata: {"id": 1}\n\n'
    stream.close()


def test_ac5_progress_printed_by_a_process_reaches_the_job_and_the_subscribers(tmp_path: Path):
    db = tmp_path / 'base.db'
    conn = connection.connect(db)
    schema.migrate(conn)
    broker = Broker()
    box = broker.subscribe()
    fake = SimpleNamespace(
        RESOURCE='gpu',
        validate=lambda params: [],
        build_command=lambda params, out_dir: [sys.executable, '-c', PRINT_PROGRESS],
    )
    worker = Worker(
        db,
        main=tmp_path,
        services={'fake': fake},
        out_root=tmp_path / 'out',
        log_dir=tmp_path / 'logs',
        poll=0.02,
        publish=broker.publish,
    )
    job_id = queue.enqueue(conn, 'fake', {}, {'fake': fake})

    worker.start()
    try:
        event = _next_event(box, lambda e: e['type'] == 'job' and e['data'].get('progress') == 0.5)
    finally:
        worker.stop()

    assert event['data']['id'] == job_id
    assert jobs.get(conn, job_id)['progress'] == 0.5
    conn.close()


def test_events_rejects_a_missing_or_wrong_token_before_streaming(api):
    # Sin token el stream no se abre: se prueba solo la respuesta de 401 (un stream real no termina en TestClient).
    assert api.client.get('/events').status_code == 401
    assert api.client.get('/events', params={'token': 'malo'}).status_code == 401
