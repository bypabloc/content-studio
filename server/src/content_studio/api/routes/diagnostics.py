"""POST /diagnostics/recording: anota un evento del micrófono en logs/recording/<día>.log (spec 010, D-7).

La app solo lo llama con el registro encendido (`diagnostics.recording_log`, apagado por defecto).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from content_studio import paths

router = APIRouter()


class RecordingEvent(BaseModel):
    """Un evento: un nombre como `record.start` y los datos que se quieran anotar."""

    event: str = Field(min_length=1, max_length=64, pattern=r'^[a-z][a-z0-9_.]*$')
    detail: dict[str, Any] = Field(default_factory=dict)


@router.post('/diagnostics/recording', status_code=204)
def record_event(body: RecordingEvent) -> None:
    """Agrega una línea JSON al archivo del día, con la hora local."""
    now = datetime.now().astimezone()
    folder = paths.LOGS / 'recording'
    folder.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {'at': now.isoformat(timespec='seconds'), 'event': body.event, 'detail': body.detail},
        ensure_ascii=False,
    )
    with (folder / f'{now:%Y-%m-%d}.log').open('a', encoding='utf-8') as file:
        file.write(line + '\n')
