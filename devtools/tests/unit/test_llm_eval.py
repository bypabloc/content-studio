"""`llm-eval` (spec 021, AC-10): chequeos por caso e informe, con el modelo y la API simulados."""

from __future__ import annotations

import json
from pathlib import Path

from devtools import llm_eval


def test_the_cases_file_has_25_script_paragraphs_and_25_cues():
    """D-6: unos 50 casos reales, mitad guion y mitad subtítulos, con id únicos."""
    cases = llm_eval.load_cases()
    assert len(cases) == 50
    assert sum(case['task'] == 'script_review' for case in cases) == 25
    assert all(case['languages'] == ['en', 'pt'] for case in cases if case['task'] == 'subtitles_translate')
    assert len({case['id'] for case in cases}) == 50


def test_check_script_reads_the_accepted_revision():
    """Sin cifras, lint limpio y la idea intacta; un párrafo descartado no conserva la idea."""
    case = {'text': 'Tienes 24 horas; es DEMO.'}
    good = {'paragraphs': [{'index': 0, 'revised': 'Tienes veinticuatro horas. Es demo.'}], 'discarded': []}
    bad = {'paragraphs': [], 'discarded': [{'index': 0}]}

    assert llm_eval.check_script(case, good) == {'no_digits': True, 'lint_clean': True, 'same_idea': True}
    assert llm_eval.check_script(case, bad) == {'no_digits': False, 'lint_clean': False, 'same_idea': False}


def test_check_cue_and_percent():
    """El cue vuelve, cabe y cambió; el porcentaje cuenta cada chequeo."""
    assert llm_eval.check_cue('Hola', {'text': 'Hello'}, (42, 2)) == {'id': True, 'fits': True, 'translated': True}
    assert llm_eval.check_cue('Hola', None, (42, 2)) == {'id': False, 'fits': False, 'translated': True}
    assert llm_eval.check_cue('Hola', {'text': 'x ' * 60}, (42, 2))['fits'] is False
    assert llm_eval.percent([{'a': True, 'b': False}, {'c': True, 'd': True}]) == 75.0
    assert llm_eval.percent([]) == 0.0


def test_vram_sampler_keeps_the_peak():
    """El muestreo guarda el máximo de VRAM visto."""
    values = iter([1000, 5200, 4800] + [4800] * 100)
    with llm_eval.VramSampler(read=lambda: next(values)) as sampler:
        import time

        time.sleep(1.2)
    assert sampler.peak == 5200


def _fake_ask(messages, rule, check=None):
    """Un modelo falso: corrige el guion y traduce cada cue a «<texto> (traducido)»."""
    content = messages[-1]['content']
    if 'CUES:' in content:
        items = json.loads(content.split('CUES:')[1])
        answer = {'cues': [{'id': item['id'], 'text': f'{item["text"]} (traducido)'} for item in items]}
    else:
        paragraphs = json.loads(content.split('linter:')[1].split('Responde')[0])
        answer = {
            'paragraphs': [
                {'index': p['index'], 'revised': 'Tienes veinticuatro horas. Es demo.', 'changes': []}
                for p in paragraphs
            ]
        }
    assert check is None or check(answer) == []
    return answer


def test_evaluate_and_report(tmp_path):
    """Con un modelo falso: resultados por tarea, tok/s y la tabla de traducciones para puntuar."""
    cases = [
        {'id': 's1', 'task': 'script_review', 'text': 'Tienes 24 horas; es DEMO.'},
        {'id': 'c1', 'task': 'subtitles_translate', 'text': 'Hola a todos.', 'languages': ['en', 'pt']},
    ]
    data = llm_eval.evaluate('gemma-4-e4b', cases, _fake_ask, [{'tokens_per_second': 40.0}], tmp_path)

    assert data['tasks']['script_review'] == {
        'cases': 1,
        'passed': 100.0,
        'latency_s': data['tasks']['script_review']['latency_s'],
    }
    assert data['tasks']['translate_pt']['passed'] == 100.0
    assert data['tokens_per_second'] == 40.0
    report = llm_eval.report({'gemma-4-e4b': {**data, 'vram_mib': 6100}}, tmp_path).read_text(encoding='utf-8')
    assert '| gemma-4-e4b | script_review | 1 | 100.0 % |' in report
    assert '| pt | Hola a todos. | Hola a todos. (traducido) |  |' in report


def test_main_without_installed_models_exits_1(tmp_path, monkeypatch, capsys):
    """Sin modelos instalados no corre nada."""
    monkeypatch.setattr(llm_eval.studio_paths, 'engines_dir', lambda: tmp_path)
    assert llm_eval.main(['--out', str(tmp_path / 'out')]) == 1
    assert 'Install llama-cpp' in capsys.readouterr().err


def test_main_runs_each_model_with_the_turn_and_writes_the_report(tmp_path, monkeypatch, capsys):
    """Con el runtime simulado: toma y suelta el turno por modelo, apaga el servidor y deja report.md."""
    from content_studio.llm import models

    for name in ('gemma-4-e4b', 'qwen3.5-9b'):
        models.gguf_path(name, tmp_path).parent.mkdir(parents=True)
        models.gguf_path(name, tmp_path).write_bytes(b'GGUF')
    models.server_path(tmp_path).parent.mkdir(parents=True)
    models.server_path(tmp_path).write_bytes(b'')
    events = []

    class FakeRuntime:
        def __init__(self, root, log):
            self.model = None

        def ensure_running(self, model):
            events.append(f'load {model}')
            return 'http://fake'

        def stop(self):
            events.append('stop')

    monkeypatch.setattr(llm_eval.studio_paths, 'engines_dir', lambda: tmp_path)
    monkeypatch.setattr(llm_eval.runtime, 'Runtime', FakeRuntime)
    monkeypatch.setattr(llm_eval.gpu_lock, 'acquire', lambda *a, **k: events.append('take') or True)
    monkeypatch.setattr(llm_eval.gpu_lock, 'release', lambda *a: events.append('release'))
    monkeypatch.setattr(llm_eval, '_nvidia_used', lambda: 3000)
    monkeypatch.setattr(
        llm_eval.client,
        'chat',
        lambda url, messages, rule, sampling, extra, check=None, stats=None: _fake_ask(messages, rule, check),
    )
    cases = tmp_path / 'cases.jsonl'
    cases.write_text(
        json.dumps({'id': 's1', 'task': 'script_review', 'text': 'Tienes 24 horas; es DEMO.'}) + '\n', encoding='utf-8'
    )

    assert llm_eval.main(['--cases', str(cases), '--out', str(tmp_path / 'out')]) == 0

    assert events == ['take', 'load gemma-4-e4b', 'stop', 'release', 'take', 'load qwen3.5-9b', 'stop', 'release']
    assert Path(json.loads(capsys.readouterr().out)['report']).is_file()
