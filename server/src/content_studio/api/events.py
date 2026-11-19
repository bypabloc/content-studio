"""Eventos en vivo (spec 004, D-4): el worker publica cada cambio de un trabajo y `GET /events` los entrega por SSE."""

from __future__ import annotations

import json
import queue
import threading
from collections.abc import Iterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


class Broker:
    """Un buzón por suscriptor. Es seguro entre hilos: el worker publica desde sus propios hilos."""

    def __init__(self) -> None:
        """Sin suscriptores todavía."""
        self._lock = threading.Lock()
        self._boxes: list[queue.Queue[dict]] = []

    def subscribe(self) -> queue.Queue[dict]:
        """Un buzón nuevo: recibe lo que se publique a partir de ahora."""
        box: queue.Queue[dict] = queue.Queue()
        with self._lock:
            self._boxes.append(box)
        return box

    def unsubscribe(self, box: queue.Queue[dict]) -> None:
        """Quita el buzón; si ya no estaba, no hace nada."""
        with self._lock:
            if box in self._boxes:
                self._boxes.remove(box)

    def publish(self, event: dict) -> None:
        """Entrega el evento a cada buzón; los buzones no tienen tope, así que no bloquea."""
        with self._lock:
            for box in self._boxes:
                box.put_nowait(event)


def encode(event: dict) -> str:
    """Un evento SSE: la línea `event:` con su tipo y la línea `data:` con el JSON."""
    return f'event: {event["type"]}\ndata: {json.dumps(event["data"], ensure_ascii=False)}\n\n'


def frames(box: queue.Queue[dict], broker: Broker) -> Iterator[str]:
    """Los eventos de un suscriptor; sin eventos, un comentario cada segundo mantiene viva la conexión."""
    try:
        while True:
            try:
                event = box.get(timeout=1.0)
            except queue.Empty:
                yield ': ping\n\n'
                continue
            yield encode(event)
    finally:
        broker.unsubscribe(box)


@router.get('/events')
def events(request: Request) -> StreamingResponse:
    """Stream `text/event-stream` con los eventos desde que el cliente se conecta."""
    broker: Broker = request.app.state.broker
    return StreamingResponse(frames(broker.subscribe(), broker), media_type='text/event-stream')
