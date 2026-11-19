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

from . import rutas

CONFIG = rutas.RAIZ / 'cspell.config.yaml'
LISTA = rutas.RAIZ / 'tmp' / 'spelling' / 'archivos.txt'


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def archivos_versionados() -> list[Path]:
    return [rutas.RAIZ / n for n in git('ls-files', cwd=rutas.RAIZ).splitlines() if n]


def archivos_staged() -> list[Path]:
    top = Path(git('rev-parse', '--show-toplevel', cwd=Path.cwd()).strip())
    return [top / n for n in git('diff', '--cached', '--name-only', '--diff-filter=ACMR', cwd=top).splitlines() if n]


def ruta_de(issue: dict) -> Path:
    return Path(url2pathname(urlparse(issue['uri']).path))


def relativa(ruta: Path) -> str:
    try:
        return ruta.relative_to(rutas.RAIZ).as_posix()
    except ValueError:
        return str(ruta)


def revisar(archivos: list[Path]) -> list[str]:
    """Una línea `archivo:línea palabra` por cada palabra que cspell no reconoce. Lanza RuntimeError si cspell falla."""
    LISTA.parent.mkdir(parents=True, exist_ok=True)
    LISTA.write_text('\n'.join(str(a) for a in archivos) + '\n', encoding='utf-8')
    orden = ['bunx', 'cspell', 'lint', '--no-progress', '--config', str(CONFIG), '--file-list', str(LISTA)]
    orden += ['--reporter', '@cspell/cspell-json-reporter']
    salida = subprocess.run(orden, cwd=rutas.RAIZ, capture_output=True, text=True, check=False)
    try:
        informe = json.loads(salida.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f'cspell no devolvió JSON: {salida.stderr.strip() or error}') from error
    if informe['result']['errors']:
        raise RuntimeError(f'cspell con {informe["result"]["errors"]} errores: {informe["error"]}')
    return [f'{relativa(ruta_de(i))}:{i["row"]} {i["text"]}' for i in informe['issues']]


def main(argv: list[str]) -> int:
    if argv and argv[0] in ('-h', '--help'):
        print('uso: spelling [--staged] [archivo ...]  (sin argumentos: todo lo versionado)', file=sys.stderr)
        return 0
    staged = '--staged' in argv
    indicados = [a for a in argv if a != '--staged']
    if any(a.startswith('-') for a in indicados):
        print('uso: spelling [--staged] [archivo ...]', file=sys.stderr)
        return 2
    if shutil.which('bun') is None:
        print('Falta bun. Instálalo y corre `bun install` en la raíz del repo.', file=sys.stderr)
        return 2
    archivos = [Path(a).resolve() for a in indicados] or (archivos_staged() if staged else archivos_versionados())
    try:
        detalle = revisar(archivos) if archivos else []
    except RuntimeError as error:
        print(f'spelling: {error}', file=sys.stderr)
        return 2
    print(json.dumps({'issues': len(detalle), 'detalle': detalle}, ensure_ascii=False))
    for linea in detalle:
        print(linea, file=sys.stderr)
    return 1 if detalle else 0
