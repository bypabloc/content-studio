"""`move-data [--apply] [--root <ruta>]`: mueve narration/ y music/ del checkout a server/data/ (spec 001, D-2).

`os.replace` es un rename dentro del mismo disco: no copia los GB de venvs, motores y modelos. Después reescribe el
prefijo de las rutas absolutas en los `.pth` y `direct_url.json` de las instalaciones editables, así que ningún venv
se recrea. Sin `--apply` solo imprime el plan. Nunca sobrescribe: si un destino tiene archivos, sale con 1.
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


def _ocupado(destino: Path) -> bool:
    if not destino.exists():
        return False
    return not destino.is_dir() or any(destino.iterdir())


def plan(root: Path) -> list[dict[str, str]]:
    """Por carpeta: `mover`, `ya migrado` (solo está en el destino), `ocupado` (el destino tiene archivos) o `nada`."""
    out = []
    for nombre in CARPETAS:
        origen, destino = root / nombre, root.joinpath(*DESTINO, nombre)
        if origen.exists():
            accion = 'ocupado' if _ocupado(destino) else 'mover'
        else:
            accion = 'ya migrado' if destino.exists() else 'nada'
        out.append({'de': str(origen), 'a': str(destino), 'accion': accion})
    return out


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
    if any(m['accion'] == 'ocupado' for m in movimientos):
        for m in movimientos:
            if m['accion'] == 'ocupado':
                sys.stderr.write(f'{m["a"]} ya tiene archivos: no se mueve {m["de"]}\n')
        print(json.dumps({'plan': movimientos, 'aplicado': False}))
        return 1
    if not aplicar:
        print(json.dumps({'plan': movimientos, 'aplicado': False}))
        return 0
    movidos = []
    for m in movimientos:
        if m['accion'] == 'mover':
            destino = Path(m['a'])
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.exists():
                destino.rmdir()  # vacío (se comprobó en plan): os.replace en Windows no reemplaza un directorio
            try:
                os.replace(m['de'], m['a'])
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
