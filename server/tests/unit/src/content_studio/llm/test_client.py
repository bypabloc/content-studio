"""Cliente de llama-server con JSON schema y un reintento, spec 021 AC-3."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from content_studio.llm import client

SCHEMA = {'type': 'object', 'properties': {'bpm': {'type': 'integer', 'maximum': 300}}, 'required': ['bpm']}


@pytest.fixture
def fake_server():
    """Un llama-server falso que responde, en orden, los contenidos de la lista y guarda cada pedido."""
    state = {'replies': [], 'requests': [], 'delay': 0.0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            state['requests'].append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            time.sleep(state['delay'])
            content = state['replies'].pop(0)
            body = json.dumps(
                {
                    'choices': [{'message': {'content': content}}],
                    'usage': {'completion_tokens': 12},
                    'timings': {'predicted_per_second': 40.0},
                }
            ).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state['url'] = f'http://127.0.0.1:{server.server_address[1]}'
    yield state
    server.shutdown()
    server.server_close()


def test_ac3_a_valid_answer_is_used_and_sends_the_schema(fake_server):
    """El pedido lleva el schema, el muestreo y los campos extra; la respuesta válida se devuelve."""
    fake_server['replies'] = ['{"bpm": 90}']
    stats = {}

    answer = client.chat(
        fake_server['url'],
        [{'role': 'user', 'content': 'hola'}],
        SCHEMA,
        {'temperature': 0.7},
        extra={'chat_template_kwargs': {'enable_thinking': False}},
        stats=stats,
    )

    assert answer == {'bpm': 90}
    sent = fake_server['requests'][0]
    assert sent['response_format']['type'] == 'json_schema'
    assert sent['response_format']['json_schema']['schema'] == SCHEMA
    assert sent['temperature'] == 0.7
    assert sent['chat_template_kwargs'] == {'enable_thinking': False}
    assert stats == {'completion_tokens': 12, 'tokens_per_second': 40.0, 'attempts': 1}


def test_ac3_an_invalid_then_valid_answer_uses_the_second(fake_server):
    """Si la primera no cumple, se reintenta una vez con el error en el mensaje."""
    fake_server['replies'] = ['{"bpm": 400}', '{"bpm": 120}']

    answer = client.chat(fake_server['url'], [{'role': 'user', 'content': 'x'}], SCHEMA, {})

    assert answer == {'bpm': 120}
    retry = fake_server['requests'][1]['messages']
    assert retry[-2] == {'role': 'assistant', 'content': '{"bpm": 400}'}
    assert '$.bpm: above 300' in retry[-1]['content']


def test_ac3_two_invalid_answers_fail_with_llm_invalid_output(fake_server):
    """Dos respuestas que no cumplen (una ni siquiera es JSON) terminan en llm_invalid_output."""
    fake_server['replies'] = ['no es json', '{"bpm": "rápido"}']

    with pytest.raises(client.LlmError) as error:
        client.chat(fake_server['url'], [{'role': 'user', 'content': 'x'}], SCHEMA, {})

    assert error.value.code == 'llm_invalid_output'
    assert len(fake_server['requests']) == 2


def test_ac3_a_failing_check_also_triggers_the_retry(fake_server):
    """La validación propia de la tarea (check) cuenta como error y provoca el reintento."""
    fake_server['replies'] = ['{"bpm": 90}', '{"bpm": 100}']

    def even(answer):
        return [] if answer['bpm'] % 20 == 0 else ['$.bpm: must be a multiple of 20']

    assert client.chat(fake_server['url'], [{'role': 'user', 'content': 'x'}], SCHEMA, {}, check=even) == {'bpm': 100}
    assert 'multiple of 20' in fake_server['requests'][1]['messages'][-1]['content']


def test_ac3_a_slow_server_fails_with_llm_timeout(fake_server):
    """Si el servidor no responde dentro del tiempo configurado, el error es llm_timeout."""
    fake_server['replies'] = ['{"bpm": 90}']
    fake_server['delay'] = 1.0

    with pytest.raises(client.LlmError) as error:
        client.chat(fake_server['url'], [{'role': 'user', 'content': 'x'}], SCHEMA, {}, timeout=0.2)

    assert error.value.code == 'llm_timeout'


def test_an_unreachable_server_fails_with_llm_unavailable():
    """Sin servidor escuchando, el error es llm_unavailable."""
    import socket

    with socket.socket() as probe:  # un puerto libre: nadie escucha ahí
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    with pytest.raises(client.LlmError) as error:  # Windows tarda ~2 s en rechazar la conexión
        client.chat(f'http://127.0.0.1:{port}', [{'role': 'user', 'content': 'x'}], SCHEMA, {}, timeout=5)

    assert error.value.code == 'llm_unavailable'
