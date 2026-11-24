"""Trabajos desde `studio` (spec 004, D-6): los flags pasan a parámetros de servicio y el trabajo corre aquí."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.db import connection, jobs, schema
from content_studio.jobs import queue
from content_studio.jobs.worker import Worker
from content_studio.messages import t
from content_studio.services.registry import SERVICES

NARRATION_FLAGS = (
    'model',
    'style',
    'voice',
    'text',
    'file',
    'profile',
    'language',
    'master',
    'lufs',
    'seed',
    'batch',
    'evaluate',
    'retries',
)
MUSIC_FLAGS = (
    'model',
    'style',
    'duration',
    'key',
    'bpm',
    'time_signature',
    'no_lm',
    'variants',
    'evaluate',
    'retries',
)
SAMPLES_FLAGS = ('styles', 'force')
OUTPUT_REFUSED = 'studio writes each job to out/<kind>/<date>-<id>-<slug>/: drop --output.'
FOLDER_REFUSED = 'studio writes each job to out/music/<date>-<id>-<slug>/: drop --folder.'


class UsageError(ValueError):
    """Un flag que `studio` no acepta para un trabajo: se muestra y sale con código 2."""


def _params(args: argparse.Namespace, flags: tuple[str, ...]) -> dict[str, Any]:
    """Los flags que se pidieron, con sus nombres de servicio; los que quedaron apagados no viajan."""
    params: dict[str, Any] = {}
    for name in flags:
        value = getattr(args, name, None)
        if value is None or value is False:
            continue
        if isinstance(value, Path):
            value = str(value)
        elif name == 'file':
            value = [str(item) for item in value]
        params[name] = value
    return params


def narration_params(args: argparse.Namespace) -> dict[str, Any]:
    """Parámetros del servicio de narración a partir de los flags de `studio narration tts`."""
    if args.output is not None:
        raise UsageError(OUTPUT_REFUSED)
    return _params(args, NARRATION_FLAGS)


def split_files(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Un trabajo por guion: cada `--file` tiene su carpeta con su blocks/ y script.json (como en la app)."""
    files = params.get('file') or []
    if len(files) < 2:
        return [params]
    return [{**params, 'file': [item]} for item in files]


def regenerate_params(args: argparse.Namespace) -> dict[str, Any]:
    """Parámetros de `narration.regenerate` a partir de `studio narration regenerate <job> <index>`."""
    params: dict[str, Any] = {'source_job': args.job, 'index': args.index}
    if args.seed is not None:
        params['seed'] = args.seed
    return params


def music_params(args: argparse.Namespace) -> dict[str, Any]:
    """Parámetros del servicio de música a partir de los flags de `studio music`."""
    if args.model is None:
        raise UsageError('the following arguments are required: --model')
    if args.folder != paths.outputs_dir() / 'music':
        raise UsageError(FOLDER_REFUSED)
    return _params(args, MUSIC_FLAGS)


def samples_params(args: argparse.Namespace) -> dict[str, Any]:
    """Parámetros de `music.samples` a partir de `studio music samples`; sin `styles`, hace todos los presets."""
    return _params(args, SAMPLES_FLAGS)


def _show_progress(event: dict) -> None:
    """Una línea en stderr por cada cambio del trabajo: su estado, su avance y la etapa."""
    if event['type'] == 'job':
        job = event['data']
        print(f'job {job["id"]}: {job["status"]} {job["progress"]:.0%} {job["stage"] or ""}'.rstrip(), file=sys.stderr)


def execute(kind: str, params: dict[str, Any], db: Path, main: Path) -> dict[str, Any] | None:
    """Encola el trabajo y lo corre en este proceso (progreso a stderr). Devuelve su job, estado y carpeta; None si el
    pedido no es válido (los motivos van a stderr)."""
    with closing(connection.connect(db)) as conn:
        schema.migrate(conn)
        try:
            job_id = queue.enqueue(conn, kind, params, SERVICES)
        except queue.InvalidJob as error:
            for item in error.errors:
                print(t(f'error.{item["code"]}', **item['params']), file=sys.stderr)
            return None
    status = Worker(db, main, publish=_show_progress).run_now(job_id)
    with closing(connection.connect(db)) as conn:
        output_dir = (jobs.get(conn, job_id) or {}).get('output_dir')
    return {'job': job_id, 'status': status, 'output_dir': output_dir}


def run(kind: str, params: dict[str, Any], db: Path, main: Path) -> int:
    """`execute` y el resultado a stdout (JSON). 0 si el trabajo terminó, 1 si falló, 2 si el pedido no es válido."""
    result = execute(kind, params, db, main)
    if result is None:
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'done' else 1
