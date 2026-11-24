"""llama-server bajo demanda, spec 021 D-1: comando por modelo, espera de /health y apagado."""

import subprocess
import sys

import pytest

from content_studio.llm import models, runtime
from content_studio.llm.client import LlmError

# Un llama-server falso: responde 200 en /health en el puerto que recibe.
FAKE = """
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == '/health' else 404)
        self.end_headers()
    def log_message(self, *a):
        pass
HTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
"""


def _install(root, model='gemma-4-e4b'):
    for path in (models.gguf_path(model, root), models.server_path(root)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'x')


def _fake_launcher(started):
    def launch(command, log):
        started.append(command)
        port = command[command.index('--port') + 1]
        return subprocess.Popen([sys.executable, '-c', FAKE, port], stdout=log, stderr=subprocess.STDOUT)

    return launch


def test_command_loads_the_gguf_with_full_offload_and_jinja(tmp_path):
    """D-1: -m con el GGUF, contexto del catálogo, -ngl 99, --jinja, sin webui y solo en 127.0.0.1."""
    command = runtime.command('qwen3.5-9b', tmp_path, 8123)

    assert command[0] == str(models.server_path(tmp_path))
    assert command[command.index('-m') + 1] == str(models.gguf_path('qwen3.5-9b', tmp_path))
    assert command[command.index('-c') + 1] == '8192'
    assert command[command.index('-ngl') + 1] == '99'
    assert command[command.index('--host') + 1] == '127.0.0.1'
    assert command[command.index('--port') + 1] == '8123'
    assert '--jinja' in command
    assert '--no-webui' in command


def test_ensure_running_waits_for_health_reuses_and_stops(tmp_path):
    """Arranca una vez, reutiliza el mismo servidor para el mismo modelo y stop() lo termina."""
    _install(tmp_path)
    started = []
    server = runtime.Runtime(tmp_path, tmp_path / 'llama.log', launch=_fake_launcher(started))
    try:
        url = server.ensure_running('gemma-4-e4b')
        assert url.startswith('http://127.0.0.1:')
        assert server.ensure_running('gemma-4-e4b') == url
        assert len(started) == 1
        assert server.model == 'gemma-4-e4b'
        process = server.process
    finally:
        server.stop()
    assert process.poll() is not None
    assert server.model is None
    server.stop()  # idempotente


def test_another_model_restarts_the_server(tmp_path):
    """Pedir otro modelo apaga el anterior y arranca uno nuevo."""
    _install(tmp_path, 'gemma-4-e4b')
    _install(tmp_path, 'qwen3.5-9b')
    started = []
    server = runtime.Runtime(tmp_path, tmp_path / 'llama.log', launch=_fake_launcher(started))
    try:
        server.ensure_running('gemma-4-e4b')
        first = server.process
        server.ensure_running('qwen3.5-9b')
        assert first.poll() is not None
        assert len(started) == 2
        assert server.model == 'qwen3.5-9b'
    finally:
        server.stop()


def test_a_missing_model_or_runtime_is_llm_not_installed(tmp_path):
    """Sin el GGUF o sin llama-server, no se lanza nada y el error es llm_not_installed."""
    server = runtime.Runtime(tmp_path, tmp_path / 'llama.log', launch=lambda command, log: pytest.fail('launched'))
    with pytest.raises(LlmError) as error:
        server.ensure_running('gemma-4-e4b')
    assert error.value.code == 'llm_not_installed'


def test_a_server_that_dies_before_health_is_llm_unavailable(tmp_path):
    """Si el proceso sale antes de responder /health (sin VRAM, GGUF roto), el error es llm_unavailable."""
    _install(tmp_path)

    def launch(command, log):
        return subprocess.Popen([sys.executable, '-c', 'raise SystemExit(3)'], stdout=log, stderr=subprocess.STDOUT)

    server = runtime.Runtime(tmp_path, tmp_path / 'llama.log', launch=launch)
    with pytest.raises(LlmError) as error:
        server.ensure_running('gemma-4-e4b')
    assert error.value.code == 'llm_unavailable'
    assert server.model is None


@pytest.mark.local
def test_local_llama_server_answers_a_json_with_the_recommended_model():
    """-m local (spec 021): llama-server real con el ★ y el turno de la GPU; responde un JSON simple y se apaga."""
    from content_studio import gpu_lock, paths
    from content_studio.common.checkout import main_checkout
    from content_studio.llm import client

    root = paths.engines_dir()
    if not models.installed(models.RECOMMENDED, root) or not models.server_path(root).is_file():
        pytest.skip('install llama-cpp and the recommended model from Engines')
    main = main_checkout(paths.ROOT)
    assert gpu_lock.acquire(main, 'pytest-local-llm', ['pytest', '-m', 'local'], wait=True, poll=5)
    server = runtime.Runtime(root)
    try:
        spec = models.MODELS[models.RECOMMENDED]
        url = server.ensure_running(models.RECOMMENDED)
        rule = {'type': 'object', 'properties': {'legs': {'type': 'integer'}}, 'required': ['legs']}
        message = [{'role': 'user', 'content': 'Responde en JSON: ¿cuántas patas tiene un perro? Campo legs.'}]
        assert client.chat(url, message, rule, spec.sampling, spec.extra, timeout=180) == {'legs': 4}
        process = server.process
    finally:
        server.stop()
        gpu_lock.release(main)
    assert process is not None and process.poll() is not None
