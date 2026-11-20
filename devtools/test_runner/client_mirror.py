"""Auditoría del espejo de client/tests/unit/src (spec 005, D-9), con la regla de la 003 para server/ y devtools/.

Cada módulo de client/src tiene su test en la ruta espejo (misma ruta y extensión, con `.test`). Los que ya existían sin
test están en `tests/validators/client-mirror.baseline.json` y solo pueden bajar: un módulo nuevo sin test falla. Los
componentes de shadcn (shared/components/shadcn), main.tsx y los `.d.ts` no se auditan.
"""

from __future__ import annotations

import json
from pathlib import Path

CLIENT_SRC = 'client/src/'
CLIENT_UNIT = 'client/tests/unit/src/'
BASELINE = 'tests/validators/client-mirror.baseline.json'
EXEMPT = ('client/src/shared/components/shadcn/', 'client/src/main.tsx')


def sources(root: Path) -> list[str]:
    """Los .ts y .tsx de client/src que necesitan su test espejo."""
    found = []
    for path in (root / 'client' / 'src').rglob('*'):
        rel = path.relative_to(root).as_posix()
        if path.suffix in ('.ts', '.tsx') and not path.name.endswith('.d.ts') and not rel.startswith(EXEMPT):
            found.append(rel)
    return sorted(found)


def mirror_of(source: str) -> str:
    """client/src/app/Shell.tsx → client/tests/unit/src/app/Shell.test.tsx."""
    stem, ext = source[len(CLIENT_SRC) :].rsplit('.', 1)
    return f'{CLIENT_UNIT}{stem}.test.{ext}'


def problems(root: Path) -> list[str]:
    """Módulos sin test espejo que no están en el baseline, y entradas del baseline que ya no aplican."""
    base = root / BASELINE
    untested = set(json.loads(base.read_text(encoding='utf-8'))['untested']) if base.is_file() else set()
    present = set(sources(root))
    issues = [
        f'{source}: no mirror test at {mirror_of(source)}'
        for source in sorted(present - untested)
        if not (root / mirror_of(source)).is_file()
    ]
    for source in sorted(untested):
        if source not in present:
            issues.append(f'{source}: in {BASELINE} but the module no longer exists: remove it from the baseline')
        elif (root / mirror_of(source)).is_file():
            issues.append(f'{source}: has its mirror test now: remove it from {BASELINE}')
    return issues
