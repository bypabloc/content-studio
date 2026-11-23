"""Validadores de los campos agregados al esquema v3 del Editor."""

from __future__ import annotations

import math
from typing import Any

BLEND_MODES = {'normal', 'multiply', 'screen', 'overlay', 'darken', 'lighten', 'add', 'difference'}


def track_error(track: dict[str, Any]) -> str | None:
    """Devuelve el error de tipo de pista o referencia de subtitulos."""
    kind = track.get('kind')
    if kind not in {'audio', 'video', 'subtitles'}:
        return 'bad_track_kind'
    if kind == 'subtitles' and (not isinstance(track.get('subtitles_project'), str) or not track['subtitles_project']):
        return 'bad_subtitles_track'
    return None


def valid_speed(value: Any) -> bool:
    """Acepta velocidades finitas entre 0,25 y 4."""
    return _finite_number(value) and 0.25 <= value <= 4


def valid_color(value: Any) -> bool:
    """Valida valores de correccion de color y la ruta opcional del LUT."""
    if not isinstance(value, dict):
        return False
    limits = {'brightness': (-1, 1), 'contrast': (0, 2), 'saturation': (0, 3), 'gamma': (0.1, 10)}
    if not all(_finite_number(value.get(key)) and low <= value[key] <= high for key, (low, high) in limits.items()):
        return False
    return 'lut' not in value or isinstance(value['lut'], str)


def valid_blend_mode(value: Any) -> bool:
    """Acepta solo los modos de fusion visibles en el Editor."""
    return isinstance(value, str) and value in BLEND_MODES


def valid_chroma(value: Any) -> bool:
    """Valida el color hexadecimal y los umbrales del chroma key."""
    if not isinstance(value, dict):
        return False
    color = value.get('color')
    return (
        isinstance(color, str)
        and len(color) == 7
        and color[0] == '#'
        and all(char in '0123456789abcdefABCDEF' for char in color[1:])
        and _between(value.get('similarity'), 0, 1)
        and _between(value.get('blend'), 0, 1)
    )


def valid_text(value: Any, raster: Any) -> bool:
    """Valida el estilo persistido y la imagen rasterizada de un clip de texto."""
    if (
        not isinstance(value, dict)
        or not isinstance(raster, str)
        or not raster.startswith('media/text-')
        or '..' in raster
    ):
        return False
    stroke, shadow, box = value.get('stroke'), value.get('shadow'), value.get('box')
    if not all(isinstance(value.get(key), str) for key in ('content', 'font', 'color')):
        return False
    if not all(_positive(value.get(key)) for key in ('weight', 'size', 'line_height', 'max_width')):
        return False
    if value.get('align') not in {'left', 'center', 'right'}:
        return False
    if not isinstance(stroke, dict) or not _between(stroke.get('width'), 0, math.inf):
        return False
    if not isinstance(stroke.get('color'), str):
        return False
    if not isinstance(shadow, dict) or not all(_finite_number(shadow.get(key)) for key in ('x', 'y', 'blur')):
        return False
    if shadow['blur'] < 0 or not isinstance(shadow.get('color'), str):
        return False
    return box is None or (
        isinstance(box, dict)
        and isinstance(box.get('color'), str)
        and _between(box.get('padding'), 0, math.inf)
        and _between(box.get('radius'), 0, math.inf)
    )


def _positive(value: Any) -> bool:
    """Acepta un numero finito positivo."""
    return _finite_number(value) and value > 0


def _between(value: Any, low: float, high: float) -> bool:
    """Comprueba un numero finito dentro de un intervalo inclusivo."""
    return _finite_number(value) and low <= value <= high


def _finite_number(value: Any) -> bool:
    """Acepta numeros finitos, pero no booleanos."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
