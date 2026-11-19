"""`move-data [--apply] [--root <ruta>]`: mueve narration/ y music/ a server/data/ y renombra los datos de narración a
inglés (spec 001, D-2, y spec 002, D-4).

Corre después del `git pull` que trae el merge: lo versionado ya lo reubicó git, así que aquí se mueve lo que no está en
git (venvs, motores, modelos, voces) y se fusiona en las carpetas que ya existen. `os.replace` es un rename dentro del
mismo disco: no copia los GB. Después reescribe el prefijo de las rutas absolutas en los `.pth` y `direct_url.json` de
las instalaciones editables, así que ningún venv se recrea. Sin `--apply` solo imprime el plan. Nunca sobrescribe: si un
destino ya existe, sale con 1 sin mover nada. Los renombres del paso 2 están en `migraciones.py`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from devtools.migrations import new
from devtools.worktree import main_checkout

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
    """Paso 2 sobre lo que deja el paso 1: (ruta actual, ruta nueva) de cada cambio, y los choques. Se calcula antes de
    mover nada, así que un choque sale con 1 sin tocar el disco."""
    data = root.joinpath(*NARRATION)
    existing = _relative_paths(root / 'narration') | _relative_paths(data)
    changes, clashes, busy = [], [], {}
    for rel in sorted(existing):
        new_path = new(rel)
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


def _forms(path: Path) -> list[str]:
    """Cómo aparece una ruta en un .pth (nativa) y en un direct_url.json (JSON escapado o con `/`)."""
    native = str(path)
    return [native, native.replace('\\', '\\\\'), path.as_posix()]


def _pares(root: Path) -> list[tuple[bytes, bytes]]:
    """Prefijos viejos y nuevos: el paso 1 (carpetas del checkout) y el paso 2 (motores, ya en server/data)."""
    changes = [(root / n, root.joinpath(*DESTINATION, n)) for n in FOLDERS]
    changes.append((root.joinpath(*NARRATION, 'motores'), root.joinpath(*NARRATION, 'engines')))
    pares = []
    for old, new_path in changes:
        pares += [(a.encode(), b.encode()) for a, b in zip(_forms(old), _forms(new_path), strict=True)]
    return pares


def _installs(data: Path):
    """Los .pth y direct_url.json de los venvs de Windows (Lib/) y de POSIX (lib/python*/)."""
    for venv in (p for p in data.rglob('.venv*') if p.is_dir()):
        for site in (venv / 'Lib/site-packages', *venv.glob('lib/python*/site-packages')):
            if site.is_dir():
                yield from site.glob('*.pth')
                yield from site.glob('*.dist-info/direct_url.json')


def rewrite(root: Path) -> list[str]:
    """Cambia el prefijo `<raíz>/narration|music` por `<raíz>/server/data/...` (y `motores` por `engines`) en las
    instalaciones editables. Idempotente: el texto nuevo no contiene el viejo."""
    changed = []
    pares = _pares(root)
    for file in _installs(root.joinpath(*DESTINATION)):
        old = file.read_bytes()
        new = old
        for a, b in pares:
            new = new.replace(a, b)
        if new != old:
            file.write_bytes(new)
            changed.append(str(file))
    return changed


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
        renamed = apply_names(root, changes)
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
