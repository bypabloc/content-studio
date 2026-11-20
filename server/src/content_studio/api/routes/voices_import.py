"""Importa un tramo de audio o video como toma (spec 010, D-4 y AC-6), con permiso del dueño."""

from __future__ import annotations

import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from content_studio import messages
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes.voices import _profile, _style
from content_studio.common import ffmpeg
from content_studio.jobs import queue
from content_studio.narration import profile_takes, profiles

router = APIRouter()
MIN_SPAN, MAX_SPAN = 8, 12  # s: la guía pide tomas de 8 a 12 s


class ImportIn(BaseModel):
    """Un tramo de un audio o un video, con el permiso del dueño (D-4)."""

    path: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    style: str
    consent: bool = False


@router.post('/voices/profiles/{slug}/import', status_code=201)
def import_span(
    slug: str, body: ImportIn, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict:
    """Extrae un tramo de 8 a 12 s de un audio o un video como toma del estilo. Sin permiso del dueño no importa nada;
    el permiso se guarda en el perfil la primera vez. El chequeo se encola como en las tomas grabadas."""
    _profile(slug)
    _style(body.style)
    if not body.consent:
        raise ApiError(422, 'consent_required')
    if not MIN_SPAN <= body.end - body.start <= MAX_SPAN:
        raise ApiError(422, 'invalid_span', low=MIN_SPAN, high=MAX_SPAN)
    with tempfile.TemporaryDirectory() as folder:
        span = Path(folder) / 'span.wav'
        try:
            ffmpeg.extract_wav(body.path, body.start, body.end, span)
        except (OSError, subprocess.CalledProcessError):
            raise ApiError(422, 'unreadable_media') from None
        take = profile_takes.save_take(slug, body.style, span.read_bytes())
    profiles.record_consent(slug, messages.t('voice.consent.import'))
    params = {'profile': slug, 'style': body.style, 'take': take}
    job = queue.enqueue(conn, 'voice.check', params, request.app.state.services)
    return {'style': body.style, 'take': take, 'job': job}


# Lo que deja elegir el diálogo de importar (el mismo filtro que el client en ImportReference.tsx).
MEDIA = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.mp4', '.mov', '.mkv', '.webm'}


@router.get('/voices/import/peaks')
def import_peaks(path: str, n: int = Query(800, ge=1, le=5000)) -> dict:
    """La duración y `n` picos de un audio o video de origen, para marcar el tramo sobre su onda (D-4). Solo acepta un
    archivo existente con extensión de audio o video; lo que ffmpeg no lee responde 422 `unreadable_media`."""
    source = Path(path)
    if source.suffix.lower() not in MEDIA or not source.is_file():
        raise ApiError(422, 'unreadable_media')
    try:
        return {'duration': ffmpeg.probe_duration(source), 'peaks': ffmpeg.peaks(source, n)}
    except (subprocess.CalledProcessError, ValueError) as error:
        raise ApiError(422, 'unreadable_media') from error
