"""`worktree prepare|close <nombre>`: worktrees de trabajo en ../content-studio-worktrees/ (regla worktrees.md).

`prepare` deja el worktree listo para correr motores: `git worktree add` solo trae lo versionado, y los venvs, los
repos de motores y los modelos pesan GB y no se mueven (codigo-python.md). Por eso los enlaza al checkout principal
(symlink en POSIX, junction en Windows, que no pide permisos de administrador) y copia los audios de referencia que
faltan, sin pisar nada. `close` borra el worktree ya fusionado en origin/dev, sus ramas y su handoff.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Carpetas ignoradas que se enlazan (globs desde la raíz) y audios que se copian.
ENLACES = ('narration/.venv*', 'music/.venv*', '.venv-*', 'narration/motores', 'music/models', 'models')
AUDIOS = ('*.wav', '*.m4a', '*.mp3', '*.flac')


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=False)


def principal(cwd: Path) -> Path:
    """Checkout principal: padre de la carpeta `.git` común (también desde un worktree)."""
    comun = _git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir').stdout.strip()
    return Path(comun).parent


def worktrees(porcelain: str) -> list[dict[str, str]]:
    """Entradas de `git worktree list --porcelain`.

    >>> worktrees('worktree /r\\nHEAD a1\\nbranch refs/heads/dev\\n\\nworktree /w/x\\nHEAD b2\\ndetached\\n')
    [{'root': '/r', 'head': 'a1', 'branch': 'dev'}, {'root': '/w/x', 'head': 'b2', 'branch': ''}]
    """
    out: list[dict[str, str]] = []
    for bloque in porcelain.strip().split('\n\n'):
        campos = dict(linea.split(' ', 1) for linea in bloque.splitlines() if ' ' in linea)
        if 'worktree' in campos:
            rama = campos.get('branch', '').removeprefix('refs/heads/')
            out.append({'root': campos['worktree'], 'head': campos.get('HEAD', ''), 'branch': rama})
    return out


def buscar(main: Path, nombre: str) -> dict[str, str] | None:
    """Worktree (que no es el principal) cuya carpeta se llama `nombre`."""
    lista = worktrees(_git(main, 'worktree', 'list', '--porcelain').stdout)
    return next((w for w in lista if Path(w['root']) != main and Path(w['root']).name == nombre), None)


def enlazar(origen: Path, destino: Path) -> None:
    """Symlink (POSIX) o junction (Windows) de la carpeta `origen` en `destino`."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        import _winapi

        _winapi.CreateJunction(str(origen), str(destino))
    else:
        destino.symlink_to(origen, target_is_directory=True)


def faltantes(main: Path, wt: Path) -> tuple[list[Path], list[Path]]:
    """Carpetas por enlazar y audios por copiar: las rutas relativas que existen en `main` y no en `wt`."""
    carpetas = [p.relative_to(main) for g in ENLACES for p in sorted(main.glob(g)) if p.is_dir()]
    voces = main / 'narration/voces'
    if voces.is_dir():
        carpetas += [p.relative_to(main) for p in sorted(voces.iterdir()) if p.is_dir()]
    audios = [p.relative_to(main) for g in AUDIOS for p in sorted((main / 'narration/voz').rglob(g))]
    falta = lambda rel: not (wt / rel).exists() and not (wt / rel).is_symlink()  # noqa: E731
    return [c for c in carpetas if falta(c)], [a for a in audios if falta(a)]


def preparar(main: Path, nombre: str) -> int:
    wt = buscar(main, nombre)
    if not wt:
        print(f'no hay un worktree llamado {nombre} (git worktree list)', file=sys.stderr)
        return 2
    root = Path(wt['root'])
    carpetas, audios = faltantes(main, root)
    for rel in carpetas:
        enlazar(main / rel, root / rel)
    for rel in audios:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(main / rel, root / rel)
    (root / 'tmp').mkdir(exist_ok=True)
    print(f'{root} listo: {len(carpetas)} carpeta(s) enlazada(s), {len(audios)} audio(s) copiado(s)', file=sys.stderr)
    print(json.dumps({'prepared': nombre, 'linked': len(carpetas), 'copied': len(audios)}))
    return 0


def es_enlace(p: Path) -> bool:
    """Symlink o junction de Windows (IO_REPARSE_TAG_MOUNT_POINT; Path.is_junction es de 3.12)."""
    return p.is_symlink() or getattr(os.lstat(p), 'st_reparse_tag', 0) == 0xA0000003


def quitar_enlaces(root: Path) -> int:
    """Quita los enlaces de `prepare` antes de borrar el worktree: `git worktree remove` no debe entrar en ellos y
    borrar los venvs o modelos del principal. Quitar un enlace (unlink o rmdir de la junction) no toca su destino."""
    enlaces = [p for g in (*ENLACES, 'narration/voces/*') for p in root.glob(g) if es_enlace(p)]
    for p in enlaces:
        p.unlink() if p.is_symlink() else os.rmdir(p)
    return len(enlaces)


def borrar_handoff(main: Path, trabajo: str) -> None:
    """Borra tmp/handoff/<trabajo>/ y los vínculos de sesión que apuntan a él."""
    base = main / 'tmp/handoff'
    shutil.rmtree(base / trabajo, ignore_errors=True)
    for vinculo in (base / '.sessions').glob('*') if (base / '.sessions').is_dir() else []:
        if vinculo.read_text(encoding='utf-8').strip() == trabajo:
            vinculo.unlink()


def cerrar(main: Path, nombre: str, trabajo: str) -> int:
    wt = buscar(main, nombre)
    if not wt:
        print(f'no hay un worktree llamado {nombre} (git worktree list)', file=sys.stderr)
        return 2
    root = Path(wt['root'])
    if Path.cwd().resolve() == root.resolve():
        print('córrelo desde el checkout principal, no desde el worktree que borra', file=sys.stderr)
        return 2
    if _git(main, 'merge-base', '--is-ancestor', wt['head'], 'origin/dev').returncode != 0:
        print(f'{wt["branch"] or nombre} no está fusionada en origin/dev (git fetch origin dev)', file=sys.stderr)
        return 1
    if _git(root, 'status', '--porcelain').stdout.strip():
        print(f'{root} tiene cambios sin confirmar o archivos sin seguimiento', file=sys.stderr)
        return 1
    quitar_enlaces(root)
    pasos = [('worktree', 'remove', '--force', str(root)), ('worktree', 'prune')]
    if wt['branch']:
        pasos.append(('branch', '-D', wt['branch']))
    for paso in pasos:
        r = _git(main, *paso)
        if r.returncode != 0:
            print(f'git {" ".join(paso)} falló: {r.stderr.strip()}', file=sys.stderr)
            return 1
    if wt['branch'] and _git(main, 'ls-remote', '--exit-code', '--heads', 'origin', wt['branch']).returncode == 0:
        _git(main, 'push', 'origin', '--delete', wt['branch'])
    borrar_handoff(main, trabajo)
    print(f'{root} cerrado', file=sys.stderr)
    print(json.dumps({'closed': nombre, 'branch': wt['branch'] or None}))
    return 0


def main(argv: list[str]) -> int:
    handoff = next((a.split('=', 1)[1] for a in argv if a.startswith('--handoff=')), None)
    args = [a for a in argv if not a.startswith('--')]
    if len(args) != 2 or args[0] not in ('prepare', 'close') or '-h' in argv or '--help' in argv:
        print('uso: worktree prepare <nombre> | worktree close <nombre> [--handoff=<trabajo>]', file=sys.stderr)
        return 0 if ('-h' in argv or '--help' in argv) else 2
    main_root = principal(Path.cwd())
    if args[0] == 'prepare':
        return preparar(main_root, args[1])
    return cerrar(main_root, args[1], handoff or args[1])
