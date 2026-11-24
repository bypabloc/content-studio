"""`python -m devtools release --installer <exe> [--dry-run]` (spec 022, D-7): arma lo que se publica en un Release.

En `tmp/release/` deja el instalador con un nombre sin espacios (`Content-Studio_<x.y.z>_x64-setup.exe`), su firma
del updater, `latest.json` (lo que consulta `tauri-plugin-updater`) y `notes.md`: los commits desde el tag anterior
por tipo (Conventional Commits) y el aviso de SmartScreen, porque el instalador no tiene firma de código (D-8).
Falla si el instalador pesa 60 MB o más (AC-6) o si falta la firma fuera de `--dry-run`. Solo stdlib.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import paths, version

REPO = 'bypabloc/content-studio'
MAX_BYTES = 60 * 1024 * 1024
OUT = 'tmp/release'
# cspell:ignore Novedades Correcciones Rendimiento
SECTIONS = {'feat': 'Novedades', 'fix': 'Correcciones', 'perf': 'Rendimiento'}
WINDOWS_NOTICE = """## Instalar en Windows

El instalador todavía no tiene firma de código: Windows puede mostrar «Windows protegió tu PC». Para seguir, elige
**Más información** y luego **Ejecutar de todas formas**. La app se instala para tu usuario, sin pedir permisos de
administrador, y después se actualiza sola desde aquí.
"""


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, encoding='utf-8', check=False)
    return done.stdout.strip() if done.returncode == 0 else ''


def notes(root: Path, tag: str) -> str:
    """Los commits entre el tag anterior y `tag` (o HEAD si `tag` no existe todavía), por sección, y el aviso."""
    head = tag if _git(root, 'rev-parse', '--verify', '--quiet', f'refs/tags/{tag}') else 'HEAD'
    previous = _git(root, 'describe', '--tags', '--abbrev=0', f'{head}^')
    span = f'{previous}..{head}' if previous else head
    grouped: dict[str, list[str]] = {name: [] for name in SECTIONS.values()}
    for subject in _git(root, 'log', '--no-merges', '--format=%s', span).splitlines():
        kind, _, text = subject.partition(': ')
        section = SECTIONS.get(kind.split('(')[0].rstrip('!'))
        if section and text:
            grouped[section].append(f'- {text}')
    body = [f'## {name}\n\n' + '\n'.join(items) + '\n' for name, items in grouped.items() if items]
    return '\n'.join([*body, WINDOWS_NOTICE])


def latest(app_version: str, signature: str, url: str, body: str) -> dict:
    """El `latest.json` del updater de Tauri 2 para Windows x64."""
    return {
        'version': app_version,
        'notes': body,
        'pub_date': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'platforms': {'windows-x86_64': {'signature': signature, 'url': url}},
    }


def main(argv: list[str], root: Path = paths.ROOT) -> int:
    """0 con las rutas en JSON; 1 si el instalador pesa de más o falta su firma; 2 si falta el instalador."""
    ap = argparse.ArgumentParser(prog='python -m devtools release', description='Stage the files of a GitHub Release.')
    ap.add_argument('--installer', required=True, type=Path, help='the NSIS .exe that tauri build made')
    ap.add_argument('--dry-run', action='store_true', help='without the updater signature: no latest.json')
    args = ap.parse_args(argv)
    app_version = version.current(root) or ''
    installer: Path = args.installer
    if not installer.is_file():
        print(f'Missing installer {installer}. Run tauri build first (docs/operations/release.md).', file=sys.stderr)
        return 2
    size = installer.stat().st_size
    if size >= MAX_BYTES:
        print(f'The installer weighs {size / 2**20:.1f} MB; the limit is 60 MB (spec 022, AC-6).', file=sys.stderr)
        return 1
    signature = installer.with_name(installer.name + '.sig')
    if not signature.is_file() and not args.dry_run:
        print(f'Missing {signature.name}: set TAURI_SIGNING_PRIVATE_KEY for tauri build.', file=sys.stderr)
        return 1
    out = root / OUT
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    tag = f'v{app_version}'
    name = f'Content-Studio_{app_version}_x64-setup.exe'
    shutil.copy2(installer, out / name)
    body = notes(root, tag)
    (out / 'notes.md').write_text(body, encoding='utf-8')
    staged = {'installer': f'{OUT}/{name}', 'notes': f'{OUT}/notes.md', 'bytes': size}
    if signature.is_file():
        shutil.copy2(signature, out / f'{name}.sig')
        url = f'https://github.com/{REPO}/releases/download/{tag}/{name}'
        manifest = latest(app_version, signature.read_text(encoding='utf-8').strip(), url, body)
        (out / 'latest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        staged.update({'signature': f'{OUT}/{name}.sig', 'latest': f'{OUT}/latest.json'})
    print(json.dumps(staged))
    return 0
