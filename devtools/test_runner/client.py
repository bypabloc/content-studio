"""Etapas `client-*` del test-runner (spec 005, D-9): cada una corre un script de client/ con bun.

El resultado es el dict de la etapa; si el script falla, `detail` es su salida (el log va al terminal).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import paths
from . import client_mirror


def _run(stage: str, command: list[str], cwd: Path) -> dict:
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return {'stage': stage, 'status': 'fail', 'detail': f'{command[0]} is not in PATH: install it and run again'}
    ok = done.returncode == 0
    return {
        'stage': stage,
        'status': 'pass' if ok else 'fail',
        'detail': '' if ok else (done.stdout + done.stderr).strip(),
    }


def _script(stage: str, script: str, root: Path) -> dict:
    return _run(stage, ['bun', 'run', script], root / 'client')


def lint(files: list[Path], root: Path = paths.ROOT) -> dict:
    """`files` no cambia el resultado: oxlint mira src y tests completos, como en la CI."""
    return _script('client-lint', 'lint', root)


# Tipos de la API generados desde `studio openapi` (D-3): la etapa los regenera y falla si el archivo cambió.
SCHEMA = 'client/src/shared/api/schema.d.ts'


def typecheck(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Regenera schema.d.ts y falla si cambió; luego `tsc --noEmit` sobre client/tsconfig.json."""
    generated = _script('client-typecheck', 'gen:api', root)
    if generated['status'] == 'fail':
        return generated
    drift = _run('client-typecheck', ['git', 'diff', '--quiet', '--', SCHEMA], root)
    if drift['status'] == 'fail':
        return {
            'stage': 'client-typecheck',
            'status': 'fail',
            'detail': f'{SCHEMA} is out of date with `studio openapi`: commit the regenerated file (gen:api).',
        }
    return _script('client-typecheck', 'typecheck', root)


def unit(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Auditoría del espejo y luego vitest con cobertura por archivo (el umbral vive en client/vite.config.ts)."""
    issues = client_mirror.problems(root)
    if issues:
        return {'stage': 'client-unit', 'status': 'fail', 'detail': '\n'.join(issues)}
    return _script('client-unit', 'test', root)


def tauri_check(files: list[Path], root: Path = paths.ROOT) -> dict:
    """`cargo check` del crate de Tauri: compila el Rust sin armar el instalador (D-9)."""
    manifest = root / 'client' / 'src-tauri' / 'Cargo.toml'
    return _run('tauri-check', ['cargo', 'check', '--manifest-path', str(manifest)], root)


def e2e(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Playwright sobre la app construida, con la API simulada (tests/e2e, D-9). Necesita Chromium instalado."""
    return _run('e2e', ['bun', 'run', 'test'], root / 'tests' / 'e2e')
