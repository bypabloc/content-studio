"""Etapa `budget` del test-runner (spec 005, D-9): el JS inicial del client, en kB gzip, contra client/budget.json.

Sin carga diferida, todo el JS del build es el inicial. El reporte va a tmp/budget/report.json (command-output.md).
"""

from __future__ import annotations

import gzip
import json
import subprocess
from pathlib import Path

from .. import paths


def measure(dist: Path) -> dict:
    """El tamaño gzip de cada `assets/*.js` del build, en kB (1 kB = 1024 bytes)."""
    files = {
        path.name: len(gzip.compress(path.read_bytes(), compresslevel=9))
        for path in sorted((dist / 'assets').glob('*.js'))
    }
    return {'total_kb': round(sum(files.values()) / 1024, 2), 'files': files}


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Build de client/ y medición contra su presupuesto. `files` no cambia el resultado."""
    build = subprocess.run(
        ['bun', 'run', 'build'],
        cwd=root / 'client',
        capture_output=True,
        encoding='utf-8',
        errors='replace',
    )
    if build.returncode:
        return {'stage': 'budget', 'status': 'fail', 'detail': (build.stdout + build.stderr).strip()}
    report = measure(root / 'client' / 'dist')
    limit = json.loads((root / 'client' / 'budget.json').read_text(encoding='utf-8'))['initialJsGzipKb']
    report['limit_kb'] = limit
    out = root / 'tmp' / 'budget' / 'report.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    ok = report['total_kb'] <= limit
    detail = '' if ok else f'{report["total_kb"]} kB gzip over the {limit} kB budget'
    return {'stage': 'budget', 'status': 'pass' if ok else 'fail', 'detail': detail}
