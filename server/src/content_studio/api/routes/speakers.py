"""Rutas de hablantes (spec 036, D-2): texto de un trabajo `transcribe`, nombres, colores y TXT (AC-5 y AC-6).

Los nombres viven en `speakers.json` de la carpeta del trabajo, no en la base.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes.jobs import JobId
from content_studio.db import jobs as store
from content_studio.diarization import exports
from content_studio.diarization import transcript_text as texts

router = APIRouter()
HEX = re.compile(r'#[0-9a-fA-F]{6}')
MAX_NAME = 40


class SpeakerIn(BaseModel):
    """Nombre y color de un hablante, como los guarda speakers.json."""

    name: str
    color: str


class ExportIn(BaseModel):
    """Cuerpo de la exportación: si el texto lleva la hora de cada bloque."""

    timestamps: bool = False


def _found(conn: sqlite3.Connection, job_id: int) -> dict:
    """El trabajo, o 404 si no existe."""
    job = store.get(conn, job_id)
    if job is None:
        raise ApiError(404, 'job_not_found', job_id=job_id)
    return job


def _folder(job: dict) -> Path:
    """La carpeta del trabajo; 409 si el trabajo no ha dejado nada todavía."""
    if not job.get('output_dir'):
        raise ApiError(409, 'no_transcript')
    return Path(job['output_dir'])


def _words(folder: Path) -> dict[str, Any]:
    """words.json de la transcripción; 409 si no está."""
    path = folder / 'words.json'
    if not path.is_file():
        raise ApiError(409, 'no_transcript')
    return json.loads(path.read_text(encoding='utf-8'))


def _speakers(folder: Path) -> dict[str, dict[str, str]]:
    """speakers.json, o un mapa vacío si el trabajo no identificó hablantes."""
    path = folder / 'speakers.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def _write_json(path: Path, data: object) -> None:
    """Escribe el JSON en un archivo temporal y lo cambia en su sitio: nunca queda a medias."""
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    os.replace(temporary, path)


def _regenerate_csv(folder: Path, speakers: dict[str, dict[str, str]]) -> None:
    """turns.csv con los nombres nuevos, si la diarización lo dejó."""
    turns_path, csv_path = folder / 'turns.json', folder / 'turns.csv'
    if turns_path.is_file() and csv_path.is_file():
        turns = json.loads(turns_path.read_text(encoding='utf-8'))
        csv_path.write_text(exports.csv_text(turns['exclusive_diarization'], speakers), encoding='utf-8')


@router.get('/jobs/{job_id}/transcript')
def transcript(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, Any]:
    """Los segmentos del trabajo con su hablante, y el mapa de nombres y colores."""
    job = _found(conn, job_id)
    folder = _folder(job)
    words = _words(folder)
    return {
        'source': job['params'].get('input'),
        'duration': words.get('duration'),
        'segments': words.get('segments', []),
        'speakers': _speakers(folder),
    }


@router.get('/jobs/{job_id}/speakers')
def get_speakers(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, Any]:
    """El mapa de hablantes; 409 si el trabajo no identificó hablantes."""
    folder = _folder(_found(conn, job_id))
    if not (folder / 'speakers.json').is_file():
        raise ApiError(409, 'not_a_diarization')
    return _speakers(folder)


@router.put('/jobs/{job_id}/speakers')
def put_speakers(
    job_id: JobId, body: dict[str, SpeakerIn], conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict[str, Any]:
    """Guarda nombres y colores; 422 si el id no existe, o el nombre o el color no son válidos."""
    folder = _folder(_found(conn, job_id))
    if not (folder / 'speakers.json').is_file():
        raise ApiError(409, 'not_a_diarization')
    current = _speakers(folder)
    changed: dict[str, dict[str, str]] = {}
    for speaker, info in body.items():
        if speaker not in current:
            raise ApiError(422, 'unknown_speaker', speaker_id=speaker)
        name = info.name.strip()
        if not 1 <= len(name) <= MAX_NAME:
            raise ApiError(422, 'invalid_speaker_name')
        if not HEX.fullmatch(info.color):
            raise ApiError(422, 'invalid_color')
        changed[speaker] = {'name': name, 'color': info.color}
    merged = {**current, **changed}
    _write_json(folder / 'speakers.json', merged)
    _regenerate_csv(folder, merged)
    return merged


@router.post('/jobs/{job_id}/transcript/export')
def export_transcript(
    job_id: JobId, body: ExportIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict[str, str]:
    """Escribe transcript.txt en la carpeta del trabajo, con los nombres actuales."""
    folder = _folder(_found(conn, job_id))
    text = texts.transcript_text(_words(folder), _speakers(folder), timestamps=body.timestamps)
    target = folder / 'transcript.txt'
    target.write_text(text, encoding='utf-8')
    return {'path': str(target)}
