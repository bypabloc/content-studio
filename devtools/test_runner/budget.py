"""Etapa `budget` del test-runner (spec 005, D-9): el JS del arranque del client, en kB gzip, contra client/budget.json.

Mide el script de entrada de dist/index.html y sus `modulepreload`: lo que baja la ventana al abrir la app.
Los chunks de `import()` (las pantallas diferidas) no cuentan. Cada archivo se comprime por separado,
como viaja por la red.
El reporte va a tmp/budget/report.json (command-output.md).
"""

from __future__ import annotations

import gzip
import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path

from .. import paths


class _Entry(HTMLParser):
    """Recoge el `src` del script de módulo y el `href` de cada `modulepreload` de index.html."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == 'script' and values.get('type') == 'module' and values.get('src'):
            self.refs.append(values['src'] or '')
        elif tag == 'link' and values.get('rel') == 'modulepreload' and values.get('href'):
            self.refs.append(values['href'] or '')


def initial_files(dist: Path) -> list[Path]:
    """Los JS que el arranque baja, según dist/index.html. Sin index.html o sin script de entrada, ninguno."""
    index = dist / 'index.html'
    if not index.is_file():
        return []
    parser = _Entry()
    parser.feed(index.read_text(encoding='utf-8'))
    names = sorted({Path(ref.split('?')[0]).name for ref in parser.refs})
    found = [dist / 'assets' / name for name in names if name.endswith('.js')]
    return [path for path in found if path.is_file()]


def measure(dist: Path) -> dict:
    """El tamaño gzip de cada JS del arranque, en kB (1 kB = 1024 bytes)."""
    files = {path.name: len(gzip.compress(path.read_bytes(), compresslevel=9)) for path in initial_files(dist)}
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
    if not report['files']:
        return {
            'stage': 'budget',
            'status': 'fail',
            'detail': 'no JS: client/dist/index.html has no entry script, so the build left no initial bundle',
        }
    limit = json.loads((root / 'client' / 'budget.json').read_text(encoding='utf-8'))['initialJsGzipKb']
    report['limit_kb'] = limit
    out = root / 'tmp' / 'budget' / 'report.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    ok = report['total_kb'] <= limit
    detail = '' if ok else f'{report["total_kb"]} kB gzip over the {limit} kB budget'
    return {'stage': 'budget', 'status': 'pass' if ok else 'fail', 'detail': detail}
