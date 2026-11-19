"""Etapa `unit`: auditoría del espejo de tests (spec 003, D-3). La cobertura se suma en el ciclo siguiente.

Cada módulo de server/src/content_studio/ y de devtools/ tiene su test en la ruta espejo. Los tests van a unit/
(server: unit/src/content_studio/), a integration/ (server) o a tdd/. La auditoría recorre todo el repo, no solo el
changeset: un módulo nuevo sin test, o un test sin módulo, falla igual. `tests/validators/mirror.baseline.json` lista
los módulos sin test que ya existían (`untested`) y los patrones exentos (`exempt`, p. ej. los motores que solo corren
en su venv).
"""

from __future__ import annotations

import json
from pathlib import Path

from .. import paths
from .validators import matches

BASELINE = 'tests/validators/mirror.baseline.json'
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


def load(root: Path) -> dict:
    path = root / BASELINE
    return (
        json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {'exempt': EXEMPT_DEFAULT, 'untested': []}
    )


def audit(root: Path) -> tuple[list[str], list[str]]:
    """(problemas, avisos) del espejo: tests fuera de lugar, huérfanos, módulos sin test y baseline obsoleto."""
    sources, tests = listed(root)
    baseline = load(root)
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


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """La auditoría mira todo el repo; `files` no cambia el resultado."""
    problems, notes = audit(root)
    return {'stage': 'unit', 'status': 'fail' if problems else 'pass', 'detail': '\n'.join(problems + notes)}


def write_baseline(root: Path = paths.ROOT) -> int:
    """Escribe los módulos sin test que hoy hay (y conserva los patrones exentos). Devuelve cuántos son."""
    sources, tests = listed(root)
    exempt = load(root).get('exempt', EXEMPT_DEFAULT)
    untested = [s for s in sources if mirror_of(s) not in tests and not any(matches(s, p) for p in exempt)]
    (root / BASELINE).write_text(
        json.dumps({'exempt': exempt, 'untested': untested}, indent=2) + '\n', encoding='utf-8'
    )
    return len(untested)
