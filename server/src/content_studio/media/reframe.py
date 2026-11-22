"""Encuadre de video (spec 015, D-3): el grafo de filtros de los cuatro modos fijos. Solo stdlib.

Cada modo produce un grafo `-filter_complex` que lee `[0:v]` y deja la salida en `[v]`, de tamaño `width` × `height`.
El modo `follow-face` (que sigue a una persona) va aparte, en T4.
"""

from __future__ import annotations

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
    raise ValueError(f'unknown reframe mode: {mode}')
