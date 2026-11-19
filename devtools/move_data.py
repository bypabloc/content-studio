"""`move-data [--apply] [--root <ruta>]`: mueve narration/ y music/ del checkout a server/data/ (spec 001, D-2).

Corre después del `git pull` que trae el merge: lo versionado ya lo reubicó git, así que aquí se mueve lo que no está en
git (venvs, motores, modelos, voces) y se fusiona en las carpetas que ya existen. `os.replace` es un rename dentro del
mismo disco: no copia los GB. Después reescribe el prefijo de las rutas absolutas en los `.pth` y `direct_url.json` de
las instalaciones editables, así que ningún venv se recrea. Sin `--apply` solo imprime el plan. Nunca sobrescribe: si un
archivo de origen ya existe en el destino, sale con 1 sin mover nada.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from devtools.worktree import principal

CARPETAS = ('narration', 'music')
DESTINO = ('server', 'data')
USO = 'uso: python -m devtools move-data [--apply] [--root <ruta>]\n'


def _colisiones(origen: Path, destino: Path) -> list[str]:
    """Archivos de `origen` que ya existen en `destino` (en las carpetas comunes, recursivo)."""
    if not destino.exists():
        return []
    if not (origen.is_dir() and destino.is_dir()):
        return [str(destino)]
    out = []
    for hijo in origen.iterdir():
        out += _colisiones(hijo, destino / hijo.name)
    return out


def plan(root: Path) -> list[dict[str, object]]:
    """Por carpeta: `mover`, `fusionar` (el destino ya existe y no choca), `colision`, `ya migrado` o `nada`."""
    out = []
    for nombre in CARPETAS:
        origen, destino = root / nombre, root.joinpath(*DESTINO, nombre)
        choques = _colisiones(origen, destino) if origen.exists() else []
        if choques:
            accion = 'colision'
        elif origen.exists():
            accion = 'fusionar' if destino.exists() else 'mover'
        else:
            accion = 'ya migrado' if destino.exists() else 'nada'
        out.append({'de': str(origen), 'a': str(destino), 'accion': accion, 'choques': choques})
    return out


def _fusionar(origen: Path, destino: Path) -> None:
    """Pasa lo de `origen` a `destino` sin sobrescribir: lo que no existe se renombra; las carpetas comunes se unen."""
    destino.mkdir(parents=True, exist_ok=True)
    for hijo in origen.iterdir():
        otro = destino / hijo.name
        if hijo.is_dir() and otro.is_dir():
            _fusionar(hijo, otro)
        else:
            os.replace(hijo, otro)
    origen.rmdir()


def _formas(ruta: Path) -> list[str]:
    """Cómo aparece una ruta en un .pth (nativa) y en un direct_url.json (JSON escapado o con `/`)."""
    nativa = str(ruta)
    return [nativa, nativa.replace('\\', '\\\\'), ruta.as_posix()]


def _pares(root: Path) -> list[tuple[bytes, bytes]]:
    pares = []
    for nombre in CARPETAS:
        viejo, nuevo = root / nombre, root.joinpath(*DESTINO, nombre)
        pares += [(a.encode(), b.encode()) for a, b in zip(_formas(viejo), _formas(nuevo), strict=True)]
    return pares


def _instalaciones(data: Path):
    """Los .pth y direct_url.json de los venvs de Windows (Lib/) y de POSIX (lib/python*/)."""
    for venv in (p for p in data.rglob('.venv*') if p.is_dir()):
        for sitio in (venv / 'Lib/site-packages', *venv.glob('lib/python*/site-packages')):
            if sitio.is_dir():
                yield from sitio.glob('*.pth')
                yield from sitio.glob('*.dist-info/direct_url.json')


def reescribir(root: Path) -> list[str]:
    """Cambia el prefijo `<raíz>/narration|music` por `<raíz>/server/data/...` en las instalaciones editables.
    Idempotente: el texto nuevo no contiene el viejo."""
    cambiados = []
    pares = _pares(root)
    for archivo in _instalaciones(root.joinpath(*DESTINO)):
        viejo = archivo.read_bytes()
        nuevo = viejo
        for a, b in pares:
            nuevo = nuevo.replace(a, b)
        if nuevo != viejo:
            archivo.write_bytes(nuevo)
            cambiados.append(str(archivo))
    return cambiados


def main(argv: list[str]) -> int:
    if any(a in ('-h', '--help') for a in argv):
        sys.stderr.write(USO)
        return 0
    aplicar = '--apply' in argv
    resto = [a for a in argv if a != '--apply']
    raiz = None
    if '--root' in resto:
        i = resto.index('--root')
        if i + 1 >= len(resto):
            sys.stderr.write(USO)
            return 2
        raiz = Path(resto[i + 1])
        del resto[i : i + 2]
    if resto:
        sys.stderr.write(f'argumento desconocido: {resto[0]}\n{USO}')
        return 2
    root = raiz or principal(Path.cwd())
    movimientos = plan(root)
    if any(m['accion'] == 'colision' for m in movimientos):
        for m in movimientos:
            for choque in m['choques']:
                sys.stderr.write(f'ya existe en el destino, no se mueve nada: {choque}\n')
        print(json.dumps({'plan': movimientos, 'aplicado': False}))
        return 1
    if not aplicar:
        print(json.dumps({'plan': movimientos, 'aplicado': False}))
        return 0
    movidos = []
    for m in movimientos:
        if m['accion'] not in ('mover', 'fusionar'):
            continue
        try:
            if m['accion'] == 'mover':
                Path(m['a']).parent.mkdir(parents=True, exist_ok=True)
                os.replace(m['de'], m['a'])
            else:
                _fusionar(Path(m['de']), Path(m['a']))
        except OSError as e:
            sys.stderr.write(f'no se pudo mover {m["de"]}: {e}. Cierra lo que lo use y vuelve a correr move-data\n')
            return 1
        movidos.append(m['a'])
    reescritos = reescribir(root)
    if not movidos:
        sys.stderr.write('ya migrado: nada que mover\n')
    for ruta in reescritos:
        sys.stderr.write(f'ruta reescrita: {ruta}\n')
    print(json.dumps({'plan': movimientos, 'movido': movidos, 'reescrito': reescritos, 'aplicado': True}))
    return 0
