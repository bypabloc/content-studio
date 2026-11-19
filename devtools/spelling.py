"""`spelling`: cspell sobre lo versionado o lo staged; sale con 1 si hay palabras desconocidas (spec 002, D-2).

Corre `bunx cspell` con `cspell.config.yaml` de la raíz. stdout = JSON en una línea; stderr = `archivo:línea palabra`.
Lo llama el pre-commit (`--staged`) y la CI. Exit 0 limpio, 1 con palabras, 2 si falta bun o cspell falla.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from . import paths

CONFIG = paths.ROOT / 'cspell.config.yaml'
LIST = paths.ROOT / 'tmp' / 'spelling' / 'files.txt'


def git(*args: str, cwd: Path) -> str:
    """Corre git con `args` en `cwd` y devuelve su salida."""
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, encoding='utf-8', check=True).stdout


def files_versioned() -> list[Path]:
    """Archivos versionados del repo, para cspell."""
    return [paths.ROOT / n for n in git('ls-files', cwd=paths.ROOT).splitlines() if n]


def files_staged() -> list[Path]:
    """Archivos en el staging, para cspell en el pre-commit."""
    top = Path(git('rev-parse', '--show-toplevel', cwd=Path.cwd()).strip())
    return [top / n for n in git('diff', '--cached', '--name-only', '--diff-filter=ACMR', cwd=top).splitlines() if n]


def path_of(issue: dict) -> Path:
    """Ruta local de un problema reportado por cspell."""
    return Path(url2pathname(urlparse(issue['uri']).path))


def relative(path: Path) -> str:
    """Ruta relativa a la raíz del repo, o la original si está fuera."""
    try:
        return path.relative_to(paths.ROOT).as_posix()
    except ValueError:
        return str(path)


def review(files: list[Path]) -> list[str]:
    """Una línea `archivo:línea palabra` por cada palabra que cspell no reconoce. Lanza RuntimeError si cspell falla."""
    LIST.parent.mkdir(parents=True, exist_ok=True)
    LIST.write_text('\n'.join(str(a) for a in files) + '\n', encoding='utf-8')
    order = ['bunx', 'cspell', 'lint', '--no-progress', '--config', str(CONFIG), '--file-list', str(LIST)]
    order += ['--reporter', '@cspell/cspell-json-reporter']
    # UTF-8 explícito: en Windows el valor por defecto es cp1252 y el JSON de cspell trae nombres con tildes.
    output = subprocess.run(order, cwd=paths.ROOT, capture_output=True, encoding='utf-8', errors='replace', check=False)
    try:
        report = json.loads(output.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f'cspell did not return JSON: {output.stderr.strip() or error}') from error
    if report['result']['errors']:
        raise RuntimeError(f'cspell with {report["result"]["errors"]} errors: {report["error"]}')
    return [f'{relative(path_of(i))}:{i["row"]} {i["text"]}' for i in report['issues']]


def main(argv: list[str]) -> int:
    """Entrada de `python -m devtools spelling`."""
    if argv and argv[0] in ('-h', '--help'):
        print('usage: spelling [--staged] [file ...]  (no arguments: all tracked files)', file=sys.stderr)
        return 0
    staged = '--staged' in argv
    indicated = [a for a in argv if a != '--staged']
    if any(a.startswith('-') for a in indicated):
        print('usage: spelling [--staged] [file ...]', file=sys.stderr)
        return 2
    if shutil.which('bun') is None:
        print('bun is missing. Install it and run `bun install` at the repo root.', file=sys.stderr)
        return 2
    files = [Path(a).resolve() for a in indicated] or (files_staged() if staged else files_versioned())
    try:
        detail = review(files) if files else []
    except RuntimeError as error:
        print(f'spelling: {error}', file=sys.stderr)
        return 2
    print(json.dumps({'issues': len(detail), 'detail': detail}))
    for line in detail:
        print(line, file=sys.stderr)
    return 1 if detail else 0
