"""Proceso de una tarea del asistente, spec 021 D-2: lee params.json, llama al modelo y deja result.json."""

import json

from content_studio.llm import task_main
from content_studio.llm.client import LlmError


def test_writes_the_result_next_to_the_params(tmp_path, monkeypatch):
    """El resultado de la tarea queda en result.json de la carpeta del trabajo; exit 0."""
    (tmp_path / 'params.json').write_text(json.dumps({'description': 'piano'}), encoding='utf-8')
    asked = {}

    def fake_chat(url, messages, rule, sampling, extra=None, check=None, timeout=120.0, stats=None):
        asked.update(url=url, sampling=sampling, extra=extra)
        return {'caption': 'soft piano', 'key': 'C Major', 'bpm': 80, 'time_signature': '4'}

    monkeypatch.setattr(task_main.client, 'chat', fake_chat)

    code = task_main.main(['music_caption', str(tmp_path), '--url', 'http://llm', '--model', 'qwen3.5-9b'])

    assert code == 0
    result = json.loads((tmp_path / 'result.json').read_text(encoding='utf-8'))
    assert result['caption'] == 'soft piano, no vocals'
    assert asked['url'] == 'http://llm'
    assert asked['extra'] == {'chat_template_kwargs': {'enable_thinking': False}}


def test_an_llm_error_exits_with_its_code(tmp_path, monkeypatch, capsys):
    """Un error del modelo sale con su código de salida y el código en stderr, para la cola."""
    (tmp_path / 'params.json').write_text(json.dumps({'description': 'piano'}), encoding='utf-8')

    def fail(*args, **kwargs):
        raise LlmError('llm_invalid_output')

    monkeypatch.setattr(task_main.client, 'chat', fail)

    code = task_main.main(['music_caption', str(tmp_path), '--url', 'http://llm', '--model', 'gemma-4-e4b'])

    assert code == task_main.EXIT_CODES['llm_invalid_output']
    assert 'llm_invalid_output' in capsys.readouterr().err
