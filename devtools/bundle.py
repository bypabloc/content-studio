"""`python -m devtools bundle` (spec 022, D-1): arma los recursos del instalador en `client/src-tauri/bundle/`.

* `bin/uv.exe`: la versión fijada de uv, verificada con su sha256 (el zip queda en `tmp/bundle/` para no bajarlo
  otra vez).
* `app/`: lo versionado de `server/` (sin sus tests) más el `pyproject.toml` y el `uv.lock` del workspace, así el
  primer arranque hace `uv sync --frozen` con el mismo lock que el repo. Solo `git ls-files`: nada de venvs ni modelos.
* `seed/`: lo que la app copia a la carpeta del usuario (`studio seed`) y su `VERSION`.

La carpeta se rehace entera en cada corrida y está en .gitignore. Solo stdlib.
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

from . import paths, version

UV_VERSION = '0.13.9'
UV_SHA256 = 'edd61f7f5728a56cc62455386661860bdfc7bab65872f39b0c25bdcc1d8e1beb'
UV_URL = f'https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-pc-windows-msvc.zip'
OUT = 'client/src-tauri/bundle'
WORKSPACE = ('pyproject.toml', 'uv.lock')
SKIP = ('server/tests/',)
SEED = {'server/data/narration/reference/default/': 'narration/reference/default/'}


class BundleError(RuntimeError):
    """Un recurso que no se pudo armar (descarga, hash o git)."""


def tracked(root: Path, prefix: str) -> list[str]:
    """Los archivos versionados bajo `prefix`, como los lista git."""
    done = subprocess.run(['git', 'ls-files', '-z', prefix], cwd=root, capture_output=True, check=False)
    if done.returncode != 0:
        raise BundleError(f'git ls-files failed in {root}: {done.stderr.decode(errors="replace").strip()}')
    return [name for name in done.stdout.decode('utf-8').split('\0') if name]


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def stage_app(root: Path, out: Path) -> int:
    """Copia el server versionado y el lock del workspace a `out/app`; devuelve cuántos archivos."""
    files = [rel for rel in tracked(root, 'server') if not rel.startswith(SKIP)] + list(WORKSPACE)
    for rel in files:
        _copy(root / rel, out / 'app' / rel)
    return len(files)


def stage_seed(root: Path, out: Path, app_version: str) -> int:
    """Copia los datos que se siembran en la carpeta del usuario y escribe `seed/VERSION`."""
    count = 0
    for prefix, target in SEED.items():
        for rel in tracked(root, prefix):
            _copy(root / rel, out / 'seed' / (target + rel[len(prefix) :]))
            count += 1
    (out / 'seed' / 'VERSION').write_text(app_version, encoding='utf-8')
    return count


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def fetch_uv(root: Path, out: Path, download: Callable[[str], bytes] = _download) -> Path:
    """`uv.exe` de la versión fijada en `out/bin`; el zip se verifica con su sha256 antes de abrirlo."""
    cached = root / 'tmp' / 'bundle' / f'uv-{UV_VERSION}.zip'
    data = cached.read_bytes() if cached.is_file() else download(UV_URL)
    digest = hashlib.sha256(data).hexdigest()
    if digest != UV_SHA256:
        raise BundleError(f'uv {UV_VERSION} has sha256 {digest}, expected {UV_SHA256}: the download was altered')
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    target = out / 'bin' / 'uv.exe'
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        target.write_bytes(archive.read('uv.exe'))
    return target


def main(argv: list[str], root: Path = paths.ROOT, download: Callable[[str], bytes] = _download) -> int:
    """0 con el resumen en JSON; 2 si falla la descarga, el hash o git."""
    if argv:
        print('usage: python -m devtools bundle', file=sys.stderr)
        return 2
    out = root / OUT
    shutil.rmtree(out, ignore_errors=True)
    try:
        app = stage_app(root, out)
        seed = stage_seed(root, out, version.current(root) or '')
        uv = fetch_uv(root, out, download)
    except (BundleError, OSError, zipfile.BadZipFile) as error:
        print(f'bundle failed: {error}', file=sys.stderr)
        return 2
    print(json.dumps({'app': app, 'seed': seed, 'uv': uv.relative_to(root).as_posix()}))
    return 0
