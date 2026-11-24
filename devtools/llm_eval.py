"""`llm-eval`: compara los modelos del asistente en español (spec 021, D-6).

Corre los casos de `tests/llm_eval/cases.jsonl` con cada modelo instalado: 25 párrafos de guion para «Revisar con IA» y
25 cues para traducir al inglés y al portugués. Cada caso tiene chequeos automáticos (guion: sin cifras, lint sin avisos
y la idea intacta; traducción: el id, el largo y que no quede igual al original). Mide el porcentaje que pasa, la
latencia media, los tok/s y la VRAM pico, con el turno de la GPU tomado. Deja `tmp/llm-eval/<fecha>/report.md`, con
una columna para que el usuario puntúe 10 traducciones de 1 a 5.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .paths import ROOT
from .worktree import main_checkout

sys.path.insert(0, str(ROOT / 'server' / 'src'))  # los módulos del asistente son solo stdlib
from content_studio import gpu_lock  # noqa: E402
from content_studio import paths as studio_paths  # noqa: E402
from content_studio.llm import client, models, runtime  # noqa: E402
from content_studio.llm.tasks import cues as cue_tools  # noqa: E402
from content_studio.llm.tasks import script_review, subtitles_translate  # noqa: E402
from content_studio.narration import script_lint  # noqa: E402
from content_studio.subtitles.document import new_document, save  # noqa: E402

CASES = ROOT / 'tests' / 'llm_eval' / 'cases.jsonl'
HUMAN_SAMPLES = 10


def load_cases(path: Path = CASES) -> list[dict]:
    """Los casos, uno por línea JSON."""
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def check_script(case: dict, result: dict) -> dict[str, bool]:
    """Guion: la propuesta aceptada no tiene cifras, el lint queda sin avisos y no se descartó por cambiar la idea."""
    accepted = {item['index']: item['revised'] for item in result['paragraphs']}
    revised = accepted.get(0, case['text'])
    return {
        'no_digits': script_lint.NUMBER.search(script_lint._visible(revised)) is None,
        'lint_clean': not script_lint.lint(revised),
        'same_idea': all(item['index'] != 0 for item in result['discarded']),
    }


def check_cue(original: str, translated: dict | None, limit: tuple[int, int]) -> dict[str, bool]:
    """Traducción: el cue volvió, cabe en el estilo y no es igual al original."""
    text = (translated or {}).get('text', '')
    return {
        'id': translated is not None,
        'fits': bool(text) and cue_tools.fits(text, limit),
        'translated': text != original,
    }


def percent(checks: list[dict[str, bool]]) -> float:
    """Porcentaje de chequeos que pasan."""
    values = [value for item in checks for value in item.values()]
    return round(100 * sum(values) / len(values), 1) if values else 0.0


class VramSampler:
    """La VRAM usada (MiB) muestreada con nvidia-smi cada medio segundo; `peak` es el máximo visto."""

    def __init__(self, read: Callable[[], int | None] | None = None) -> None:
        """`read` se reemplaza en las pruebas."""
        self.read = read or _nvidia_used
        self.peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self) -> None:
        while not self._stop.wait(0.5):
            self.peak = max(self.peak, self.read() or 0)

    def __enter__(self) -> VramSampler:
        """Toma la primera muestra y arranca el muestreo."""
        self.peak = self.read() or 0
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        """Detiene el muestreo."""
        self._stop.set()
        self._thread.join()


def _nvidia_used() -> int | None:
    if not shutil.which('nvidia-smi'):
        return None
    done = subprocess.run(
        ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0 or not done.stdout.strip():
        return None
    used, total = (int(value) for value in done.stdout.split(',')[:2])
    return used if used <= total else None


def evaluate(model: str, cases: list[dict], ask: Callable[..., dict], stats: list[dict], work: Path) -> dict:
    """Los casos con un modelo ya cargado: chequeos, latencia y tok/s por tarea, y las traducciones de muestra."""
    script_checks, script_times = [], []
    for case in (item for item in cases if item['task'] == 'script_review'):
        start = time.monotonic()
        result = script_review.run({'text': case['text'], 'all': True}, ask)
        script_times.append(time.monotonic() - start)
        script_checks.append(check_script(case, result))
    cue_cases = [item for item in cases if item['task'] == 'subtitles_translate']
    tasks: dict[str, dict] = {'script_review': _summary(script_checks, script_times)}
    samples: dict[str, list[dict]] = {}
    for language in sorted({lang for item in cue_cases for lang in item['languages']}):
        doc = work / f'{model}-{language}.json'
        source = [
            {'id': i, 'start': 2.0 * i, 'end': 2.0 * i + 1.8, 'text': c['text'], 'words': []}
            for i, c in enumerate(cue_cases, 1)
        ]
        save(new_document(source_path='llm-eval', kind='import', language='es', cues=source), doc)
        start = time.monotonic()
        result = subtitles_translate.run({'doc': str(doc), 'language': language}, ask)
        elapsed = (time.monotonic() - start) / max(len(source), 1)
        by_id = {cue['id']: cue for cue in result['cues']}
        checks = [check_cue(cue['text'], by_id.get(cue['id']), cue_tools.DEFAULT_LIMITS) for cue in source]
        tasks[f'translate_{language}'] = _summary(checks, [elapsed] * len(checks))
        samples[language] = [
            by_id.get(cue['id'], {'original': cue['text'], 'text': ''}) for cue in source[:HUMAN_SAMPLES]
        ]
    speeds = [item['tokens_per_second'] for item in stats if item.get('tokens_per_second')]
    return {
        'tasks': tasks,
        'tokens_per_second': round(sum(speeds) / len(speeds), 1) if speeds else 0.0,
        'samples': samples,
    }


def _summary(checks: list[dict[str, bool]], times: list[float]) -> dict:
    return {
        'cases': len(checks),
        'passed': percent(checks),
        'latency_s': round(sum(times) / len(times), 2) if times else 0.0,
    }


def _sample(data: dict, language: str, index: int) -> dict:
    samples = data['samples'].get(language) or []
    return samples[index] if index < len(samples) else {}


def report(results: dict[str, dict], out: Path) -> Path:
    """report.md: lo que pasa, la latencia, los tok/s y la VRAM por modelo y tarea, y la tabla para puntuar."""
    lines = [
        '# llm-eval',
        '',
        '| Model | Task | Cases | Pass | Latency (s) | tok/s | Peak VRAM (MiB) |',
        '| :--- | :--- | ---: | ---: | ---: | ---: | ---: |',
    ]
    for model, data in results.items():
        speed, vram = data['tokens_per_second'], data['vram_mib']
        for task, row in data['tasks'].items():
            measures = f'{row["cases"]} | {row["passed"]} % | {row["latency_s"]} | {speed} | {vram}'
            lines.append(f'| {model} | {task} | {measures} |')
    names = ' | '.join(results)
    lines += ['', '## Translations to score (1 to 5)', '', f'| Language | Original | {names} | Score |']
    lines.append('| :--- | :--- |' + ' :--- |' * len(results) + ' :---: |')
    for language in sorted({lang for data in results.values() for lang in data['samples']}):
        for index in range(HUMAN_SAMPLES):
            items = [_sample(data, language, index) for data in results.values()]
            original = next((item.get('original', '') for item in items if item), '')
            if original:
                texts = ' | '.join(item.get('text', '') for item in items)
                lines.append(f'| {language} | {original} | {texts} |  |')
    target = out / 'report.md'
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return target


def _run_model(model: str, cases: list[dict], root: Path, out: Path, main_dir: Path) -> dict:
    """Un modelo con el turno de la GPU: lo carga, corre los casos, mide la VRAM y lo apaga."""
    print(f'llm-eval: {model}', file=sys.stderr)
    gpu_lock.acquire(main_dir, 'llm-eval', ['llm-eval', model], wait=True)
    server = runtime.Runtime(root, ROOT / 'logs' / 'llama-server-llm-eval.log')
    stats: list[dict] = []
    spec = models.MODELS[model]
    try:
        with VramSampler() as vram:
            url = server.ensure_running(model)

            def ask(messages: list[dict], rule: dict, check: Callable | None = None) -> dict:
                stats.append({})
                return client.chat(url, messages, rule, spec.sampling, spec.extra, check=check, stats=stats[-1])

            data = evaluate(model, cases, ask, stats, out)
        return {**data, 'vram_mib': vram.peak}
    finally:
        server.stop()
        gpu_lock.release(main_dir)


def main(argv: list[str]) -> int:
    """Corre la prueba con los modelos instalados y deja el informe. Exit 1 si no hay modelos instalados."""
    ap = argparse.ArgumentParser(
        prog='python -m devtools llm-eval', description='compare the assistant models in Spanish'
    )
    ap.add_argument('--models', nargs='+', choices=sorted(models.MODELS), help='default: every installed model')
    ap.add_argument('--cases', type=Path, default=CASES)
    ap.add_argument('--out', type=Path, default=ROOT / 'tmp' / 'llm-eval' / datetime.now().strftime('%Y-%m-%d-%H%M'))
    args = ap.parse_args(argv)
    root = studio_paths.engines_dir()
    chosen = [name for name in args.models or sorted(models.MODELS) if models.installed(name, root)]
    if not chosen or not models.server_path(root).is_file():
        print('No assistant model is installed. Install llama-cpp and a model from Engines.', file=sys.stderr)
        return 1
    cases = load_cases(args.cases)
    args.out.mkdir(parents=True, exist_ok=True)
    main_dir = main_checkout(ROOT)
    results = {model: _run_model(model, cases, root, args.out, main_dir) for model in chosen}
    (args.out / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'report': str(report(results, args.out)), 'models': chosen}))
    return 0
