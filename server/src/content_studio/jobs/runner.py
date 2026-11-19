"""Corre el comando de un trabajo: el progreso va a la base y el resto del stdout y el stderr a logs/jobs/<id>.log."""

from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path

from content_studio import paths
from content_studio.common import progress
from content_studio.db import jobs


def run(conn: sqlite3.Connection, job_id: int, command: list[str], log_dir: Path = paths.LOGS / 'jobs') -> int:
    """Ejecuta `command` y devuelve su código de salida. Cada `@@progress` actualiza el trabajo."""
    log_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    with (
        (log_dir / f'{job_id}.log').open('w', encoding='utf-8') as log,
        subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
        ) as proc,
    ):
        assert proc.stdout is not None  # stdout=PIPE
        for line in proc.stdout:
            report = progress.parse(line)
            if report:
                jobs.update(conn, job_id, progress=report['p'], stage=report.get('stage'))
            else:
                log.write(line)
        return proc.wait()
