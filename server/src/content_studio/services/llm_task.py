"""Servicios de las tareas del asistente (spec 021, D-2): un trabajo `llm.<tarea>` por tarea, con recurso gpu.

El worker agrega a los params `llm_url` y `llm_model` (el llama-server caliente); el resto viaja en params.json.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from content_studio.llm.task_main import EXIT_CODES, TASKS

RESOURCE = 'gpu'
ERROR_CODES = {code: detail for detail, code in EXIT_CODES.items()}


def service(task: str) -> SimpleNamespace:
    """El servicio de una tarea: su validación y el comando de task_main."""

    def build_command(params: dict, output_dir: Path) -> list[str]:
        return [
            sys.executable,
            '-m',
            'content_studio.llm.task_main',
            task,
            str(output_dir),
            '--url',
            params['llm_url'],
            '--model',
            params['llm_model'],
        ]

    return SimpleNamespace(
        RESOURCE=RESOURCE,
        ERROR_CODES=ERROR_CODES,
        prepare=getattr(TASKS[task], 'prepare', None),  # las de subtítulos resuelven el proyecto
        validate=TASKS[task].validate,
        build_command=build_command,
    )
