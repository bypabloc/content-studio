"""Jerarquía de imports del client (spec 008, D-4): avisos de oxlint sobre fixtures con el `.oxlintrc.json` real.

La regla vive en `client/.oxlintrc.json`, en los `overrides` de `no-restricted-imports`. Este módulo solo copia los
archivos a un client/ temporal, para que los `files` de esos overrides apliquen, y devuelve los avisos de la regla por
archivo. Lo usa `devtools/tests/unit/test_runner/test_client_lint_hierarchy.py`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .. import paths

OXLINT = paths.ROOT / 'node_modules' / '.bin' / ('oxlint.exe' if os.name == 'nt' else 'oxlint')
RULE = 'eslint(no-restricted-imports)'


def restricted_imports(
    names: list[str],
    fixtures: Path,
    tmp: Path,
    config: Path = paths.ROOT / 'client' / '.oxlintrc.json',
) -> dict[str, list[str]]:
    """Avisos de `no-restricted-imports` por archivo: los fixtures van a `tmp/client/` con `config`."""
    client = tmp / 'client'
    client.mkdir(parents=True, exist_ok=True)
    shutil.copy(config, client / '.oxlintrc.json')
    for name in names:
        target = client / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(fixtures / name, target)
    done = subprocess.run(
        [str(OXLINT), '-c', '.oxlintrc.json', '--format', 'json', *names],
        cwd=client,
        capture_output=True,
        encoding='utf-8',
        errors='replace',
        check=False,
    )
    return _hits(done.stdout, names)


def _hits(output: str, names: list[str]) -> dict[str, list[str]]:
    """Los mensajes de la regla, agrupados por el archivo de `names` al que pertenecen."""
    report = json.loads(output or '{"diagnostics": []}')
    hits: dict[str, list[str]] = {}
    for diagnostic in report['diagnostics']:
        if diagnostic.get('code') != RULE:
            continue
        filename = Path(diagnostic['filename']).as_posix()
        for name in names:
            if filename.endswith(name):
                # `help` lleva el texto que pone cada override; `message`, el genérico de oxlint.
                hits.setdefault(name, []).append(diagnostic.get('help') or diagnostic['message'])
    return hits
