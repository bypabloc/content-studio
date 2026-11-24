"""Siembra de la app instalada (spec 022, D-3): copia `<recursos>/seed` a la carpeta de datos sin pisar lo del usuario.

`.seeded.json` guarda la versión y el sha256 de cada archivo sembrado. Un archivo que falta se copia; uno que el
usuario no tocó desde la siembra pasa a la versión nueva; uno que cambió queda igual, con `<archivo>.new` al lado.
Debajo de `narration/reference/` (los perfiles del usuario) solo se crea lo que falta. Solo stdlib.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from content_studio import paths

MANIFEST = '.seeded.json'
PROTECTED = ('narration/reference/',)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed(source: Path, target: Path) -> dict:
    """Siembra `source` en `target`; devuelve la versión y cuántos archivos copió, actualizó y conservó."""
    version_file = source / 'VERSION'
    version = version_file.read_text(encoding='utf-8').strip() if version_file.is_file() else ''
    manifest_path = target / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.is_file() else {}
    files: dict[str, str] = dict(manifest.get('files', {}))
    counts = {'copied': 0, 'updated': 0, 'kept': 0}
    for path in sorted(item for item in source.rglob('*') if item.is_file() and item != version_file):
        rel = path.relative_to(source).as_posix()
        dest, new = target / rel, _sha(path)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            files[rel] = new
            counts['copied'] += 1
            continue
        current = _sha(dest)
        if current == new:
            files[rel] = new
        elif rel.startswith(PROTECTED):
            continue
        elif files.get(rel) == current:  # sembrado y sin cambios del usuario: pasa a la versión nueva
            shutil.copy2(path, dest)
            files[rel] = new
            counts['updated'] += 1
        else:
            copy = dest.with_name(dest.name + '.new')
            if not copy.is_file() or _sha(copy) != new:
                shutil.copy2(path, copy)
                counts['kept'] += 1
                print(f'seed: kept {rel}, changed by the user; the new version is in {copy.name}', file=sys.stderr)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({'version': version, 'files': files}, indent=2), encoding='utf-8')
    return {'version': version, **counts}


def cli() -> int:
    """`studio seed`: en la app instalada siembra sus recursos; en un checkout no hay nada que sembrar."""
    resources = paths.resources_dir()
    if resources is None:
        print(json.dumps({'skipped': 'not_installed'}))
        return 0
    print(json.dumps(seed(resources / 'seed', paths.data_dir())))
    return 0
