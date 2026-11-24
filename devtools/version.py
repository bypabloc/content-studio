"""`python -m devtools version <x.y.z> | --check [--expect x.y.z]` (spec 022, D-7): la versión de la app de una vez.

`tauri.conf.json` es la referencia. `version <x.y.z>` escribe la versión en los manifiestos (y en la entrada
`content-studio` de `Cargo.lock` y `uv.lock`, para que un build no deje el árbol sucio). `--check` sale con 1 y nombra
el archivo si alguno difiere; `--expect` compara además con el tag de la release. Solo stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import paths

REFERENCE = 'client/src-tauri/tauri.conf.json'
_JSON = r'(?m)^(  "version": ")([^"]+)(")'
MANIFESTS = {
    REFERENCE: _JSON,
    'client/package.json': _JSON,
    'package.json': _JSON,
    'client/src-tauri/Cargo.toml': r'(\[package\][^\[]*?\nversion = ")([^"]+)(")',
    'server/pyproject.toml': r'(\[project\][^\[]*?\nversion = ")([^"]+)(")',
    'client/src-tauri/Cargo.lock': r'(name = "content-studio"\r?\nversion = ")([^"]+)(")',
    'uv.lock': r'(name = "content-studio"\r?\nversion = ")([^"]+)(")',
}
SEMVER = re.compile(r'\d+\.\d+\.\d+')


def _text(root: Path, rel: str) -> str:
    return (root / rel).read_bytes().decode('utf-8')


def read(root: Path = paths.ROOT) -> dict[str, str | None]:
    """La versión de la app en cada manifiesto (None si el archivo no la tiene)."""
    found: dict[str, str | None] = {}
    for rel, pattern in MANIFESTS.items():
        match = re.search(pattern, _text(root, rel))
        found[rel] = match.group(2) if match else None
    return found


def current(root: Path = paths.ROOT) -> str | None:
    """La versión de la app: la de `tauri.conf.json`."""
    match = re.search(MANIFESTS[REFERENCE], _text(root, REFERENCE))
    return match.group(2) if match else None


def write(new: str, root: Path = paths.ROOT) -> None:
    """Escribe `new` en cada manifiesto; el resto del archivo (y sus fines de línea) queda igual."""
    for rel, pattern in MANIFESTS.items():
        text = re.sub(pattern, lambda match: match.group(1) + new + match.group(3), _text(root, rel), count=1)
        (root / rel).write_bytes(text.encode('utf-8'))


def problems(root: Path = paths.ROOT, expect: str | None = None) -> list[str]:
    """Cada manifiesto cuya versión no es la de `tauri.conf.json` (o `expect`); vacío fuera del repo."""
    if not (root / REFERENCE).is_file():
        return []
    found = read(root)
    wanted = expect or found[REFERENCE]
    return [f'{rel}: {value} (expected {wanted})' for rel, value in found.items() if value != wanted]


def main(argv: list[str], root: Path = paths.ROOT) -> int:
    """0 bien; 1 si un manifiesto difiere; 2 si la versión no es x.y.z."""
    ap = argparse.ArgumentParser(prog='python -m devtools version', description='The app version in every manifest.')
    ap.add_argument('version', nargs='?', help='new version, x.y.z')
    ap.add_argument('--check', action='store_true', help='fail if a manifest has another version')
    ap.add_argument('--expect', help='with --check: the version the release tag asks for')
    args = ap.parse_args(argv)
    for value in (args.version, args.expect):
        if value is not None and not SEMVER.fullmatch(value):
            print(f'Invalid version {value!r}: use x.y.z (semver), e.g. 0.2.0.', file=sys.stderr)
            return 2
    if args.version is None and not args.check:
        ap.print_usage(sys.stderr)
        return 2
    if args.version is not None:
        write(args.version, root)
    found = problems(root, args.expect)
    for line in found:
        print(f'version mismatch: {line}. Run python -m devtools version <x.y.z>.', file=sys.stderr)
    print(json.dumps({'version': args.expect or read(root)[REFERENCE]}))
    return 1 if found else 0
