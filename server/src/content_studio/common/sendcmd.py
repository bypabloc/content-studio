"""Órdenes de `sendcmd` y `asendcmd` de ffmpeg: el archivo de tiempos y la ruta que el grafo lee (specs 015 y 016).

Sin `eval`: el ffmpeg de este equipo no lo trae. Solo stdlib.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


def script(orders: Iterable[tuple[float, str]]) -> str:
    """Un archivo de órdenes: `<segundos> <destino> <orden> <valor>;`, una por línea.

    >>> print(script([(0, 'crop x 176'), (0.2, 'crop x 1136')]), end='')
    0.000000 crop x 176;
    0.200000 crop x 1136;
    """
    return ''.join(f'{t:.6f} {order};\n' for t, order in orders)


def filter_path(path: Path | str) -> str:
    r"""Ruta para `f='…'` entre comillas: barras hacia adelante y `:` escapado (la unidad de Windows).

    >>> filter_path('C:/x/follow.txt')
    'C\\:/x/follow.txt'
    """
    return Path(path).as_posix().replace(':', '\\:')
