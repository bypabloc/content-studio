"""`worktree prepare|close <nombre>`: worktrees de trabajo en ../content-studio-worktrees/ (regla worktrees.md).

`prepare` deja el worktree listo para correr motores: `git worktree add` solo trae lo versionado, y los venvs, los
repos de motores y los modelos pesan GB y no se mueven (codigo-python.md). Por eso los enlaza al checkout principal
(symlink en POSIX, junction en Windows, que no pide permisos de administrador) y copia los audios de referencia que
faltan, sin pisar nada. `close` borra el worktree ya fusionado en origin/dev y sus ramas.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Carpetas ignoradas que se enlazan (globs desde la raíz) y audios que se copian.
LINKS = (
    'server/data/narration/.venv*',
    'server/data/music/.venv*',
    'server/data/narration/engines',
    'server/data/music/models',
    'node_modules',  # diccionarios de cspell: sin ellos `spelling` (y el pre-commit) falla en el worktree
)
VOZ, VOCES = 'server/data/narration/reference', 'server/data/narration/voices'
AUDIOS = ('*.wav', '*.m4a', '*.mp3', '*.flac')


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=False)


def main_checkout(cwd: Path) -> Path:
    """Checkout principal: padre de la carpeta `.git` común (también desde un worktree)."""
    common = _git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir').stdout.strip()
    return Path(common).parent


def worktrees(porcelain: str) -> list[dict[str, str]]:
    """Entradas de `git worktree list --porcelain`.

    >>> worktrees('worktree /r\\nHEAD a1\\nbranch refs/heads/dev\\n\\nworktree /w/x\\nHEAD b2\\ndetached\\n')
    [{'root': '/r', 'head': 'a1', 'branch': 'dev'}, {'root': '/w/x', 'head': 'b2', 'branch': ''}]
    """
    out: list[dict[str, str]] = []
    for block in porcelain.strip().split('\n\n'):
        campos = dict(line.split(' ', 1) for line in block.splitlines() if ' ' in line)
        if 'worktree' in campos:
            rama = campos.get('branch', '').removeprefix('refs/heads/')
            out.append({'root': campos['worktree'], 'head': campos.get('HEAD', ''), 'branch': rama})
    return out


def search(main: Path, name: str) -> dict[str, str] | None:
    """Worktree (que no es el principal) cuya carpeta se llama `nombre`."""
    list = worktrees(_git(main, 'worktree', 'list', '--porcelain').stdout)
    return next((w for w in list if Path(w['root']) != main and Path(w['root']).name == name), None)


def link(source: Path, destination: Path) -> None:
    """Symlink (POSIX) o junction (Windows) de la carpeta `origen` en `destino`."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        import _winapi

        _winapi.CreateJunction(str(source), str(destination))
    else:
        destination.symlink_to(source, target_is_directory=True)


def missing(main: Path, wt: Path) -> tuple[list[Path], list[Path]]:
    """Carpetas por enlazar y audios por copiar: las rutas relativas que existen en `main` y no en `wt`."""
    folders = [p.relative_to(main) for g in LINKS for p in sorted(main.glob(g)) if p.is_dir()]
    voces = main / VOCES
    if voces.is_dir():
        folders += [p.relative_to(main) for p in sorted(voces.iterdir()) if p.is_dir()]
    audios = [p.relative_to(main) for g in AUDIOS for p in sorted((main / VOZ).rglob(g))]
    absent = lambda rel: not (wt / rel).exists() and not (wt / rel).is_symlink()  # noqa: E731
    return [c for c in folders if absent(c)], [a for a in audios if absent(a)]


def prepare(main: Path, name: str) -> int:
    """Enlaza venvs, motores, modelos y voces del principal en el worktree `name`."""
    wt = search(main, name)
    if not wt:
        print(f'there is no worktree named {name} (git worktree list)', file=sys.stderr)
        return 2
    root = Path(wt['root'])
    folders, audios = missing(main, root)
    for rel in folders:
        link(main / rel, root / rel)
    for rel in audios:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(main / rel, root / rel)
    (root / 'tmp').mkdir(exist_ok=True)
    print(f'{root} ready: {len(folders)} folder(s) linked, {len(audios)} audio file(s) copied', file=sys.stderr)
    print(json.dumps({'prepared': name, 'linked': len(folders), 'copied': len(audios)}))
    return 0


def is_link(p: Path) -> bool:
    """Symlink o junction de Windows (IO_REPARSE_TAG_MOUNT_POINT; Path.is_junction es de 3.12)."""
    return p.is_symlink() or getattr(os.lstat(p), 'st_reparse_tag', 0) == 0xA0000003


def remove_links(root: Path) -> int:
    """Quita los enlaces de `prepare` antes de borrar el worktree: `git worktree remove` no debe entrar en ellos y
    borrar los venvs o modelos del principal. Quitar un enlace (unlink o rmdir de la junction) no toca su destino."""
    links = [p for g in (*LINKS, f'{VOCES}/*') for p in root.glob(g) if is_link(p)]
    for p in links:
        p.unlink() if p.is_symlink() else os.rmdir(p)
    return len(links)


def close(main: Path, name: str) -> int:
    """Cierra el worktree `name` fusionado en origin/dev y borra sus enlaces y ramas."""
    wt = search(main, name)
    if not wt:
        print(f'there is no worktree named {name} (git worktree list)', file=sys.stderr)
        return 2
    root = Path(wt['root'])
    if Path.cwd().resolve() == root.resolve():
        print('run it from the main checkout, not from the worktree being deleted', file=sys.stderr)
        return 2
    if _git(main, 'merge-base', '--is-ancestor', wt['head'], 'origin/dev').returncode != 0:
        print(f'{wt["branch"] or name} is not merged into origin/dev (git fetch origin dev)', file=sys.stderr)
        return 1
    if _git(root, 'status', '--porcelain').stdout.strip():
        print(f'{root} has uncommitted changes or untracked files', file=sys.stderr)
        return 1
    remove_links(root)
    steps = [('worktree', 'remove', '--force', str(root)), ('worktree', 'prune')]
    if wt['branch']:
        steps.append(('branch', '-D', wt['branch']))
    for step in steps:
        r = _git(main, *step)
        if r.returncode != 0 and step[1] == 'remove' and not search(main, name):
            # Windows: git ya vació y desregistró el worktree, pero un proceso con cwd ahí retiene la carpeta.
            try:
                root.rmdir()
            except OSError:
                print(f'{root} is unregistered but still on disk (held by a process): delete it later', file=sys.stderr)
            continue
        if r.returncode != 0:
            print(f'git {" ".join(step)} failed: {r.stderr.strip()}', file=sys.stderr)
            return 1
    if wt['branch'] and _git(main, 'ls-remote', '--exit-code', '--heads', 'origin', wt['branch']).returncode == 0:
        _git(main, 'push', 'origin', '--delete', wt['branch'])
    print(f'{root} closed', file=sys.stderr)
    print(json.dumps({'closed': name, 'branch': wt['branch'] or None}))
    return 0


def main(argv: list[str]) -> int:
    """Entrada de `python -m devtools worktree`: prepare o close."""
    args = [a for a in argv if not a.startswith('--')]
    if len(args) != 2 or args[0] not in ('prepare', 'close') or '-h' in argv or '--help' in argv:
        print('usage: worktree prepare <name> | worktree close <name>', file=sys.stderr)
        return 0 if ('-h' in argv or '--help' in argv) else 2
    main_root = main_checkout(Path.cwd())
    if args[0] == 'prepare':
        return prepare(main_root, args[1])
    return close(main_root, args[1])
