"""Encuadre de video (spec 015, D-3): el grafo de filtros de los modos de encuadre. Solo stdlib.

Cada modo produce un grafo `-filter_complex` que lee `[0:v]` y deja la salida en `[v]`, de tamaño `width` × `height`.
Los cuatro modos fijos van con su tamaño. `follow-face` recorta con `crop` y mueve el recorte con `sendcmd`, según las
posiciones que dejó `vision/face_track_main` (AC-5).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def graph(reframe: dict[str, Any], width: int, height: int) -> str:
    """El grafo de filtros del encuadre `reframe` (`{mode, ...}`) para una salida de `width` × `height`.

    >>> graph({'mode': 'center'}, 1080, 1920)
    '[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]'
    """
    mode = reframe['mode']
    if mode == 'center':
        return f'[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[v]'
    if mode == 'manual':
        x, y, w, h = reframe['x'], reframe['y'], reframe['w'], reframe['h']
        return f'[0:v]crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},scale={width}:{height}[v]'
    if mode == 'fit-bars':
        color = reframe.get('color', 'black')
        return (
            f'[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,'
            f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={color}[v]'
        )
    if mode == 'fit-blur':
        strength = reframe.get('strength', 20)
        return (
            '[0:v]split[bg][fg];'
            f'[bg]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},boxblur={strength}[blurred];'
            f'[fg]scale={width}:{height}:force_original_aspect_ratio=decrease[sharp];'
            '[blurred][sharp]overlay=(W-w)/2:(H-h)/2[v]'
        )
    if mode == 'follow-face':
        commands = _filter_path(reframe['commands'])
        crop_w = reframe['crop_w']
        chain = f"sendcmd=f='{commands}',crop=w={crop_w}:h=ih:x=0:y=0,scale={width}:{height}"
        return f'[0:v]{chain}[v]'
    raise ValueError(f'unknown reframe mode: {mode}')


def crop_width(source_height: int, width: int, height: int) -> int:
    """El ancho del recorte con la proporción de salida, a la altura de la fuente; par, como lo pide yuv420p."""
    return 2 * round(source_height * width / height / 2)


def crop_xs(centers: list[float], source_width: int, crop_w: int) -> list[int]:
    """La esquina izquierda del recorte para cada posición (0–1) de la cara: centrada en ella, par y en el cuadro."""
    limit = source_width - crop_w
    return [min(limit, max(0, _even(round(center * source_width - crop_w / 2)))) for center in centers]


def sendcmd_script(xs: list[int], fps: float) -> str:
    """Las órdenes de `sendcmd` para mover `crop x`: una por muestra, a 1/`fps` s de la anterior."""
    return ''.join(f'{index / fps:.6f} crop x {x};\n' for index, x in enumerate(xs))


def _even(value: int) -> int:
    return value // 2 * 2


def _filter_path(path: str) -> str:
    """La ruta para un argumento de filtro: barras hacia adelante y los dos puntos de la unidad escapados."""
    return Path(path).as_posix().replace(':', '\\:')
