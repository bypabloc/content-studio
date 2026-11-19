"""Etapa `unit`: pytest con cobertura por archivo y auditoría del espejo de tests (spec 003, D-3 y D-4).

Cada módulo de server/src/content_studio/ y de devtools/ tiene su test en la ruta espejo. Los tests van a unit/
(server: unit/src/content_studio/), a integration/ (server) o a tdd/. La auditoría recorre todo el repo, no solo el
changeset: un módulo nuevo sin test, o un test sin módulo, falla igual. `tests/validators/mirror.baseline.json` lista
los módulos sin test que ya existían (`untested`) y los patrones exentos (`exempt`, p. ej. los motores que solo corren
en su venv). La cobertura exige COVERAGE_MIN por archivo del changeset; `tests/validators/coverage.baseline.json` lista
los archivos por debajo del mínimo que ya existían.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .. import paths
from .validators import matches

BASELINE = 'tests/validators/mirror.baseline.json'
COVERAGE_BASELINE = 'tests/validators/coverage.baseline.json'
COVERAGE_JSON = 'tmp/test-runner/coverage.json'
PYTEST_LOG = 'tmp/test-runner/pytest.log'
COVERAGE_MIN = 80
COVERAGE_OMIT = ['*/engines/*', 'server/src/content_studio/cli/*', 'server/src/content_studio/narration/grabar/*']
SERVER_SRC = 'server/src/content_studio/'
SERVER_UNIT = 'server/tests/unit/src/content_studio/'
EXEMPT_DEFAULT = ['server/src/content_studio/*/engines/*.py']
ALLOWED_TESTS = {
    'server/tests/': ('server/tests/unit/src/content_studio/', 'server/tests/integration/', 'server/tests/tdd/'),
    'devtools/tests/': ('devtools/tests/unit/', 'devtools/tests/tdd/'),
}


def mirror_of(source: str) -> str:
    """server/src/content_studio/a/b.py → server/tests/unit/src/content_studio/a/test_b.py (devtools: sin `src/`)."""
    if source.startswith(SERVER_SRC):
        base, rest = SERVER_UNIT, source[len(SERVER_SRC) :]
    else:
        base, rest = 'devtools/tests/unit/', source[len('devtools/') :]
    head, _, name = rest.rpartition('/')
    return base + (head + '/' if head else '') + 'test_' + name


def source_of(test: str) -> str:
    """Inversa de mirror_of para un test unitario."""
    if test.startswith(SERVER_UNIT):
        base, rest = SERVER_SRC, test[len(SERVER_UNIT) :]
    else:
        base, rest = 'devtools/', test[len('devtools/tests/unit/') :]
    head, _, name = rest.rpartition('/')
    return base + (head + '/' if head else '') + name[len('test_') :]


def listed(root: Path) -> tuple[list[str], list[str]]:
    """(módulos fuente, tests) del repo, relativos y en posix."""
    sources = [
        p.relative_to(root).as_posix()
        for base in ('server/src/content_studio', 'devtools')
        for p in (root / base).rglob('*.py')
        if p.name != '__init__.py' and not p.relative_to(root).as_posix().startswith('devtools/tests/')
    ]
    tests = [
        p.relative_to(root).as_posix()
        for base in ('server/tests', 'devtools/tests')
        for p in (root / base).rglob('test_*.py')
    ]
    return sorted(sources), sorted(tests)


def load(root: Path, name: str = BASELINE) -> Any:
    """Lee el JSON `name` del repo; vacío si no existe."""
    path = root / name
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def audit(root: Path) -> tuple[list[str], list[str]]:
    """(problemas, avisos) del espejo: tests fuera de lugar, huérfanos, módulos sin test y baseline obsoleto."""
    sources, tests = listed(root)
    baseline = load(root) or {'exempt': EXEMPT_DEFAULT, 'untested': []}
    problems, notes = [], []
    for test in tests:
        prefix = next(p for p in ALLOWED_TESTS if test.startswith(p))
        if not test.startswith(ALLOWED_TESTS[prefix]):
            problems.append(f'misplaced test: {test} (put it in unit/, integration/ or tdd/)')
        elif test.startswith(('server/tests/unit/', 'devtools/tests/unit/')) and source_of(test) not in sources:
            problems.append(f'orphan test: {test} (no module {source_of(test)})')
    tested = set(tests)
    for source in sources:
        if any(matches(source, pattern) for pattern in baseline.get('exempt', [])):
            continue
        if mirror_of(source) in tested:
            if source in baseline.get('untested', []):
                notes.append(f'{source}: has its test now, remove it from {BASELINE}')
        elif source not in baseline.get('untested', []):
            problems.append(f'no test: {source} (expected {mirror_of(source)})')
    return problems, notes


def in_scope(rel: str) -> bool:
    """Módulos que miden cobertura: producto y devtools, sin los motores (corren en su venv), cli/ ni grabar/."""
    return (
        rel.startswith(('server/src/content_studio/', 'devtools/'))
        and rel.endswith('.py')
        and not rel.startswith('devtools/tests/')
        and not rel.endswith('__init__.py')
        and not any(matches(rel, pattern) for pattern in COVERAGE_OMIT)
    )


def check_coverage(report: dict, scope: list[str], baseline: list[str]) -> list[str]:
    """Un problema por archivo del alcance bajo COVERAGE_MIN; un archivo sin medida cuenta como 0 %."""
    measured = {Path(name).as_posix(): data['summary']['percent_covered'] for name, data in report['files'].items()}
    problems = []
    for rel in scope:
        if rel in baseline:
            continue
        percent = measured.get(rel, 0.0)
        if percent < COVERAGE_MIN:
            problems.append(f'{rel}: {percent:g}% covered (min {COVERAGE_MIN}%)')
    return problems


def coverage_report(root: Path) -> tuple[int, dict]:
    """Corre pytest con cobertura; el log va a tmp/test-runner/pytest.log. Devuelve (exit de pytest, informe)."""
    out = root / COVERAGE_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    command = [
        'uv',
        'run',
        'pytest',
        '-q',
        '--cov=server/src/content_studio',
        '--cov=devtools',
        f'--cov-report=json:{out}',
    ]
    data = {**os.environ, 'COVERAGE_FILE': str(root / 'tmp/test-runner/.coverage')}  # fuera de la raíz
    done = subprocess.run(command, cwd=root, capture_output=True, encoding='utf-8', errors='replace', env=data)
    (root / PYTEST_LOG).write_text(done.stdout + done.stderr, encoding='utf-8')
    report = json.loads(out.read_text(encoding='utf-8')) if out.is_file() else {'files': {}}
    return done.returncode, report


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Auditoría del espejo sobre todo el repo, pytest completo y cobertura de los `files` del alcance."""
    problems, notes = audit(root)
    code, report = coverage_report(root)
    if code:
        problems.append(f'pytest failed (exit {code}): see {PYTEST_LOG}')
    scope = [rel for rel in (p.relative_to(root).as_posix() for p in files) if in_scope(rel)]
    problems += check_coverage(report, scope, load(root, COVERAGE_BASELINE) or [])
    return {'stage': 'unit', 'status': 'fail' if problems else 'pass', 'detail': '\n'.join(problems + notes)}


def write_baseline(root: Path = paths.ROOT) -> int:
    """Escribe los módulos sin test que hoy hay (y conserva los patrones exentos). Devuelve cuántos son."""
    sources, tests = listed(root)
    exempt = (load(root) or {}).get('exempt', EXEMPT_DEFAULT)
    untested = [s for s in sources if mirror_of(s) not in tests and not any(matches(s, p) for p in exempt)]
    (root / BASELINE).write_text(
        json.dumps({'exempt': exempt, 'untested': untested}, indent=2) + '\n', encoding='utf-8'
    )
    return len(untested)


def write_coverage_baseline(root: Path = paths.ROOT) -> int:
    """Escribe los archivos del alcance que hoy están bajo COVERAGE_MIN. Corre pytest completo."""
    _, report = coverage_report(root)
    below = [rel for rel in listed(root)[0] if in_scope(rel) and check_coverage(report, [rel], [])]
    (root / COVERAGE_BASELINE).write_text(json.dumps(below, indent=2) + '\n', encoding='utf-8')
    return len(below)
