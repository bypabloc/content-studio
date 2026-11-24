"""`move-data [--apply] [--root <ruta>]`: mueve narration/ y music/ a server/data/ y renombra los datos de narración a
inglés (spec 001, D-2, y spec 002, D-4).

Corre después del `git pull` que trae el merge: lo versionado ya lo reubicó git, así que aquí se mueve lo que no está en
git (venvs, motores, modelos, voces) y se fusiona en las carpetas que ya existen. `os.replace` es un rename dentro del
mismo disco: no copia los GB. Después reescribe el prefijo de las rutas absolutas en los `.pth` y `direct_url.json` de
las instalaciones editables, así que ningún venv se recrea. Sin `--apply` solo imprime el plan. Nunca sobrescribe: si un
destino ya existe, sale con 1 sin mover nada. Los renombres de los pasos 2 y 3 están en `migrations.py`.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from devtools.migrations import new, profile_path
from devtools.worktree import main_checkout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server' / 'src'))

from content_studio.storage.relocate import rewrite_installs  # noqa: E402

FOLDERS = ('narration', 'music')
DESTINATION = ('server', 'data')
NARRATION = (*DESTINATION, 'narration')
USO = 'usage: python -m devtools move-data [--apply] [--root <path>]\n'


def _collisions(source: Path, destination: Path) -> list[str]:
    """Archivos de `origen` que ya existen en `destino` (en las carpetas comunes, recursivo)."""
    if not destination.exists():
        return []
    if not (source.is_dir() and destination.is_dir()):
        return [str(destination)]
    out = []
    for child in source.iterdir():
        out += _collisions(child, destination / child.name)
    return out


def plan(root: Path) -> list[dict[str, object]]:
    """Por carpeta: `mover`, `fusionar` (el destino ya existe y no choca), `colision`, `ya migrado` o `nada`."""
    out = []
    for name in FOLDERS:
        source, destination = root / name, root.joinpath(*DESTINATION, name)
        clashes = _collisions(source, destination) if source.exists() else []
        if clashes:
            action = 'collision'
        elif source.exists():
            action = 'merge' if destination.exists() else 'move'
        else:
            action = 'already migrated' if destination.exists() else 'nothing'
        out.append({'from': str(source), 'to': str(destination), 'action': action, 'clashes': clashes})
    return out


# cspell:ignore motores: nombre viejo de la carpeta en disco que este comando renombra (D-4).
def _relative_paths(folder: Path) -> set[str]:
    """Archivos de `carpeta` con rutas relativas y `/`. No entra en `motores/`: esa carpeta se renombra entera."""
    found = set()
    for actual, dirs, files in os.walk(folder):
        source = Path(actual)
        dirs[:] = [s for s in dirs if source != folder or s != 'motores']
        found.update((source / a).relative_to(folder).as_posix() for a in files)
    return found


def plan_names(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Pasos 2 y 3 sobre lo que deja el paso 1: (ruta actual, ruta nueva) de cada cambio, y los choques.
    Se calcula antes de mover nada, así que un choque sale con 1 sin tocar el disco."""
    data = root.joinpath(*NARRATION)
    existing = _relative_paths(root / 'narration') | _relative_paths(data)
    changes, clashes, busy = [], [], {}
    for rel in sorted(existing):
        new_path = profile_path(new(rel))
        if new_path == rel:
            continue
        if new_path in existing or new_path in busy:
            clashes.append(f'{new_path} (de {rel})')
        else:
            busy[new_path] = rel
            changes.append((rel, new_path))
    if (root / 'narration' / 'motores').exists() or (data / 'motores').exists():
        if (data / 'engines').exists():
            clashes.append('engines (from motores)')
        else:
            changes.append(('motores', 'engines'))
    return changes, clashes


def _remove_empty(folder: Path, cap: Path) -> None:
    """Borra las carpetas que un movimiento dejó vacías, subiendo hasta `tope`. Las que tienen contenido no se tocan."""
    while folder != cap and folder.is_dir() and not any(folder.iterdir()):
        folder.rmdir()
        folder = folder.parent


def apply_names(root: Path, changes: list[tuple[str, str]]) -> list[str]:
    """Renombra los archivos de datos a su nombre en inglés; no pisa los que ya existen."""
    data = root.joinpath(*NARRATION)
    for rel, new_path in changes:
        source, destination = data / rel, data / new_path
        if destination.exists():
            raise FileExistsError(str(destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)
        _remove_empty(source.parent, data)
    return [f'{rel} -> {new_path}' for rel, new_path in changes]


def ensure_default_profile(root: Path) -> list[str]:
    """Paso 3: el perfil default se llama «Mi voz». Si su carpeta ya existe y no tiene profile.json, lo crea."""
    folder = root.joinpath(*NARRATION, 'reference', 'default')
    target = folder / 'profile.json'
    if not folder.is_dir() or target.exists():
        return []
    data = {'name': 'Mi voz', 'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return [str(target)]


def _merge(source: Path, destination: Path) -> None:
    """Pasa lo de `origen` a `destino` sin sobrescribir: lo que no existe se renombra; las carpetas comunes se unen."""
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        other = destination / child.name
        if child.is_dir() and other.is_dir():
            _merge(child, other)
        else:
            os.replace(child, other)
    source.rmdir()


def rewrite(root: Path) -> list[str]:
    """Cambia el prefijo `<raíz>/narration|music` por `<raíz>/server/data/...` (y `motores` por `engines`) en las
    instalaciones editables. Idempotente: el texto nuevo no contiene el viejo."""
    changes = [(root / name, root.joinpath(*DESTINATION, name)) for name in FOLDERS]
    changes.append((root.joinpath(*NARRATION, 'motores'), root.joinpath(*NARRATION, 'engines')))
    return rewrite_installs(root.joinpath(*DESTINATION), changes)


def main(argv: list[str]) -> int:
    """Entrada de `python -m devtools move-data`: sin --apply solo imprime el plan."""
    if any(a in ('-h', '--help') for a in argv):
        sys.stderr.write(USO)
        return 0
    apply = '--apply' in argv
    rest = [a for a in argv if a != '--apply']
    root = None
    if '--root' in rest:
        i = rest.index('--root')
        if i + 1 >= len(rest):
            sys.stderr.write(USO)
            return 2
        root = Path(rest[i + 1])
        del rest[i : i + 2]
    if rest:
        sys.stderr.write(f'unknown argument: {rest[0]}\n{USO}')
        return 2
    root = root or main_checkout(Path.cwd())
    moves = plan(root)
    changes, clashes = plan_names(root)
    names = [f'{rel} -> {new}' for rel, new in changes]
    if any(m['action'] == 'collision' for m in moves) or clashes:
        for m in moves:
            for clash in m['clashes']:
                sys.stderr.write(f'already exists in the destination, nothing is moved: {clash}\n')
        for clash in clashes:
            sys.stderr.write(f'already exists in the destination, nothing is moved: {clash}\n')
        print(json.dumps({'plan': moves, 'names': names, 'applied': False}))
        return 1
    if not apply:
        print(json.dumps({'plan': moves, 'names': names, 'applied': False}))
        return 0
    moved = []
    for m in moves:
        if m['action'] not in ('move', 'merge'):
            continue
        try:
            if m['action'] == 'move':
                Path(m['to']).parent.mkdir(parents=True, exist_ok=True)
                os.replace(m['from'], m['to'])
            else:
                _merge(Path(m['from']), Path(m['to']))
        except OSError as e:
            sys.stderr.write(f'could not move {m["from"]}: {e}. Close whatever uses it and run move-data again\n')
            return 1
        moved.append(m['to'])
    try:
        renamed = apply_names(root, changes) + ensure_default_profile(root)
    except OSError as e:
        sys.stderr.write(f'could not rename: {e}. Close whatever uses it and run move-data again\n')
        return 1
    rewritten = rewrite(root)
    if not moved and not renamed:
        sys.stderr.write('already migrated: nothing to move\n')
    for path in rewritten:
        sys.stderr.write(f'path rewritten: {path}\n')
    print(json.dumps({'plan': moves, 'moved': moved, 'names': renamed, 'rewritten': rewritten, 'applied': True}))
    return 0
