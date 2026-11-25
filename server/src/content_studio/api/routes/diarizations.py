"""Diarización por la API (spec 037): el resultado de un trabajo `diarize` (AC-4) y su proyecto del Editor (AC-6).

Los archivos los escribe `content_studio.diarization` en la carpeta del trabajo; aquí solo se leen.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from content_studio import paths
from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.api.routes.jobs import JobId
from content_studio.db import jobs as store
from content_studio.editor import store as projects
from content_studio.editor.from_diarization import project_from_diarization

router = APIRouter()


class FromDiarizationIn(BaseModel):
    """El trabajo `diarize` del que sale el proyecto."""

    job: int


def _diarize_job(conn: sqlite3.Connection, job_id: int) -> tuple[dict[str, Any], Path]:
    """El trabajo `diarize` terminado y su carpeta: 404 si no existe, 409 si no es una diarización o no tiene turnos."""
    job = store.get(conn, job_id)
    if job is None:
        raise ApiError(404, 'job_not_found', job_id=job_id)
    if job['kind'] != 'diarize':
        raise ApiError(409, 'not_a_diarization')
    if not job.get('output_dir') or not (Path(job['output_dir']) / 'turns.json').is_file():
        raise ApiError(409, 'no_diarization')
    return job, Path(job['output_dir'])


def _speakers(folder: Path) -> dict[str, dict[str, str]]:
    """speakers.json: el nombre y el color de cada hablante; vacío si el archivo no existe."""
    path = folder / 'speakers.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def _split(conn: sqlite3.Connection, folder: Path) -> dict[str, str] | None:
    """Un WAV por hablante del último `diarize.split` terminado de esta diarización; None si no hay ninguno.

    El split escribe en su propia carpeta de trabajo, así que se busca por el trabajo que apunta a `folder`.
    """
    done = [
        job
        for job in store.list_jobs(conn, kind='diarize.split', status='done')
        if Path(job['params'].get('turns', '')) == folder
    ]
    if not done:
        return None
    latest = max(done, key=lambda job: job['id'])
    if not latest.get('output_dir'):
        return None
    speakers = Path(latest['output_dir']) / 'speakers'
    wavs = {path.stem: str(path) for path in sorted(speakers.glob('*.wav'))} if speakers.is_dir() else {}
    return wavs or None


@router.get('/diarizations/{job_id}')
def diarization(job_id: JobId, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, Any]:
    """Turnos, hablantes, archivos y audios por hablante de un trabajo diarize (spec 037, AC-4)."""
    job, folder = _diarize_job(conn, job_id)
    turns = json.loads((folder / 'turns.json').read_text(encoding='utf-8'))
    return {
        'source': job['params']['input'],
        'duration': turns['duration'],
        'turns': turns['diarization'],
        'exclusive_turns': turns['exclusive_diarization'],
        'speakers': _speakers(folder),
        'files': {
            'json': str(folder / 'turns.json'),
            'rttm': str(folder / 'turns.rttm'),
            'csv': str(folder / 'turns.csv'),
        },
        'split': _split(conn, folder),
    }


@router.post('/editor/projects/from-diarization', status_code=201)
def project_from_job(body: FromDiarizationIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict[str, str]:
    """Crea un proyecto del Editor con el audio y un marcador por turno; devuelve la ruta de su project.json (AC-6)."""
    job, folder = _diarize_job(conn, body.job)
    turns = json.loads((folder / 'turns.json').read_text(encoding='utf-8'))
    doc = project_from_diarization(
        job['params']['input'], turns['duration'], turns['exclusive_diarization'], _speakers(folder)
    )
    file = projects.create(paths.outputs_dir() / 'editor', doc['name'], date.today())
    _, digest = projects.read(file)
    projects.write(file, doc, digest)
    return {'project': str(file)}
