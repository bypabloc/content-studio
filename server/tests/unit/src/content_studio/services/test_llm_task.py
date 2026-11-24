"""Servicios de las tareas del asistente, spec 021 D-2."""

import sys

from content_studio.services import llm_task
from content_studio.services.registry import SERVICES


def test_every_task_is_a_gpu_service():
    """Cada tarea es un trabajo llm.<tarea> con recurso gpu y sus códigos de error."""
    for name in llm_task.TASKS:
        service = SERVICES[f'llm.{name}']
        assert service.RESOURCE == 'gpu'
        assert service.ERROR_CODES[llm_task.EXIT_CODES['llm_invalid_output']] == 'llm_invalid_output'


def test_build_command_passes_the_url_and_model_from_the_worker(tmp_path):
    """El worker agrega llm_url y llm_model; el comando corre task_main con la carpeta del trabajo."""
    command = SERVICES['llm.music_caption'].build_command(
        {'description': 'piano', 'llm_url': 'http://127.0.0.1:9', 'llm_model': 'gemma-4-e4b'}, tmp_path
    )

    assert command[:3] == [sys.executable, '-m', 'content_studio.llm.task_main']
    assert command[3:] == ['music_caption', str(tmp_path), '--url', 'http://127.0.0.1:9', '--model', 'gemma-4-e4b']


def test_validate_delegates_to_the_task():
    """La validación es la de la tarea."""
    assert SERVICES['llm.music_caption'].validate({'description': ''})
    assert SERVICES['llm.script_review'].validate({'text': 'Hola.'}) == []
