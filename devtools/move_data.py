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

from devtools.migraciones import nuevo
from devtools.worktree import principal

CARPETAS = ('narration', 'music')
DESTINO = ('server', 'data')
NARRACION = (*DESTINO, 'narration')
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


def _relativos(carpeta: Path) -> set[str]:
    """Archivos de `carpeta` con rutas relativas y `/`. No entra en `motores/`: esa carpeta se renombra entera."""
    rels = set()
    for actual, subcarpetas, archivos in os.walk(carpeta):
        origen = Path(actual)
        subcarpetas[:] = [s for s in subcarpetas if origen != carpeta or s != 'motores']
        rels.update((origen / a).relative_to(carpeta).as_posix() for a in archivos)
    return rels


def plan_nombres(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Paso 2 sobre lo que deja el paso 1: (ruta actual, ruta nueva) de cada cambio, y los choques. Se calcula antes de
    mover nada, así que un choque sale con 1 sin tocar el disco."""
    datos = root.joinpath(*NARRACION)
    rels = _relativos(root / 'narration') | _relativos(datos)
    cambios, choques, ocupados = [], [], {}
    for rel in sorted(rels):
        nueva = nuevo(rel)
        if nueva == rel:
            continue
        if nueva in rels or nueva in ocupados:
            choques.append(f'{nueva} (de {rel})')
        else:
            ocupados[nueva] = rel
            cambios.append((rel, nueva))
    if (root / 'narration' / 'motores').exists() or (datos / 'motores').exists():
        if (datos / 'engines').exists():
            choques.append('engines (de motores)')
        else:
            cambios.append(('motores', 'engines'))
    return cambios, choques


def _quitar_vacios(carpeta: Path, tope: Path) -> None:
    """Borra las carpetas que un movimiento dejó vacías, subiendo hasta `tope`. Las que tienen contenido no se tocan."""
    while carpeta != tope and carpeta.is_dir() and not any(carpeta.iterdir()):
        carpeta.rmdir()
        carpeta = carpeta.parent


def aplicar_nombres(root: Path, cambios: list[tuple[str, str]]) -> list[str]:
    datos = root.joinpath(*NARRACION)
    for rel, nueva in cambios:
        origen, destino = datos / rel, datos / nueva
        if destino.exists():
            raise FileExistsError(str(destino))
        destino.parent.mkdir(parents=True, exist_ok=True)
        os.replace(origen, destino)
        _quitar_vacios(origen.parent, datos)
    return [f'{rel} -> {nueva}' for rel, nueva in cambios]


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
    """Prefijos viejos y nuevos: el paso 1 (carpetas del checkout) y el paso 2 (motores, ya en server/data)."""
    cambios = [(root / n, root.joinpath(*DESTINO, n)) for n in CARPETAS]
    cambios.append((root.joinpath(*NARRACION, 'motores'), root.joinpath(*NARRACION, 'engines')))
    pares = []
    for viejo, nuevo_ in cambios:
        pares += [(a.encode(), b.encode()) for a, b in zip(_formas(viejo), _formas(nuevo_), strict=True)]
    return pares


def _instalaciones(data: Path):
    """Los .pth y direct_url.json de los venvs de Windows (Lib/) y de POSIX (lib/python*/)."""
    for venv in (p for p in data.rglob('.venv*') if p.is_dir()):
        for sitio in (venv / 'Lib/site-packages', *venv.glob('lib/python*/site-packages')):
            if sitio.is_dir():
                yield from sitio.glob('*.pth')
                yield from sitio.glob('*.dist-info/direct_url.json')


def reescribir(root: Path) -> list[str]:
    """Cambia el prefijo `<raíz>/narration|music` por `<raíz>/server/data/...` (y `motores` por `engines`) en las
    instalaciones editables. Idempotente: el texto nuevo no contiene el viejo."""
    cambiados = []
    pares = _pares(root)
    for archivo in _instalaciones(root.joinpath(*DESTINO)):
        viejo = archivo.read_bytes()
        nuevo_ = viejo
        for a, b in pares:
            nuevo_ = nuevo_.replace(a, b)
        if nuevo_ != viejo:
            archivo.write_bytes(nuevo_)
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
    cambios, choques = plan_nombres(root)
    nombres = [f'{rel} -> {nueva}' for rel, nueva in cambios]
    if any(m['accion'] == 'colision' for m in movimientos) or choques:
        for m in movimientos:
            for choque in m['choques']:
                sys.stderr.write(f'ya existe en el destino, no se mueve nada: {choque}\n')
        for choque in choques:
            sys.stderr.write(f'ya existe en el destino, no se mueve nada: {choque}\n')
        print(json.dumps({'plan': movimientos, 'nombres': nombres, 'aplicado': False}))
        return 1
    if not aplicar:
        print(json.dumps({'plan': movimientos, 'nombres': nombres, 'aplicado': False}))
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
    try:
        renombrados = aplicar_nombres(root, cambios)
    except OSError as e:
        sys.stderr.write(f'no se pudo renombrar: {e}. Cierra lo que lo use y vuelve a correr move-data\n')
        return 1
    reescritos = reescribir(root)
    if not movidos and not renombrados:
        sys.stderr.write('ya migrado: nada que mover\n')
    for ruta in reescritos:
        sys.stderr.write(f'ruta reescrita: {ruta}\n')
    print(
        json.dumps(
            {'plan': movimientos, 'movido': movidos, 'nombres': renombrados, 'reescrito': reescritos, 'aplicado': True}
        )
    )
    return 0
