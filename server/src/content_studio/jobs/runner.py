"""Corre el comando de un trabajo: el progreso va a la base y el resto del stdout y el stderr a logs/jobs/<id>.log."""

from __future__ import annotations

import os
import sqlite3
import subprocess
from collections.abc import Callable
from pathlib import Path

from content_studio import paths
from content_studio.common import progress
from content_studio.db import jobs


def run(
    conn: sqlite3.Connection,
    job_id: int,
    command: list[str],
    log_dir: Path = paths.LOGS / 'jobs',
    register: Callable[[subprocess.Popen], None] | None = None,
    on_progress: Callable[[], None] | None = None,
) -> int:
    """Ejecuta `command` y devuelve su código de salida. Cada `@@progress` actualiza el trabajo.

    `register` recibe el proceso al arrancar, para que el worker lo pueda cancelar; `on_progress` avisa tras cada
    actualización. En POSIX corre en su propio grupo de procesos, así se terminan también los hijos.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    database = conn.execute('PRAGMA database_list').fetchone()[2]
    if database:
        env['CONTENT_STUDIO_DB'] = database
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
            start_new_session=os.name != 'nt',
        ) as proc,
    ):
        if register:
            register(proc)
        assert proc.stdout is not None  # stdout=PIPE
        for line in proc.stdout:
            report = progress.parse(line)
            if report:
                jobs.update(conn, job_id, progress=report['p'], stage=report.get('stage'))
                if on_progress:
                    on_progress()
            else:
                log.write(line)
        return proc.wait()
