"""Estilos y presets de subtítulos (spec 014, D-5). Datos y funciones puras; solo stdlib.

Los colores van en `#RRGGBB` o `#RRGGBBAA` (AA es la opacidad, como en CSS); `ass_color` los pasa a ASS.
"""

from __future__ import annotations

import copy
from typing import Any

BASE: dict[str, Any] = {
    'font': 'Arial',
    'size': 48,
    'bold': False,
    'color': '#FFFFFF',
    'outline_color': '#000000',
    'outline': 3,
    'shadow': 0,
    'back_box': None,
    'position': 'bottom',
    'margin_v': 60,
    'uppercase': False,
    'mode': 'classic',
    'words_per_cue': None,
    'highlight_color': '#FFD400',
    'pop': False,
}

PRESETS: dict[str, dict[str, Any]] = {
    'classic': {**BASE},
    'reels': {
        **BASE,
        'font': 'Montserrat ExtraBold',
        'size': 72,
        'bold': True,
        'position': 'middle',
        'margin_v': 0,
        'uppercase': True,
        'mode': 'social',
        'words_per_cue': 2,
        'pop': True,
    },
    'karaoke': {**BASE, 'mode': 'karaoke'},
    'minimal': {**BASE, 'size': 36, 'back_box': '#00000080'},
}

ALIGNMENT = {'bottom': 2, 'middle': 5, 'top': 8}


def preset(name: str) -> dict[str, Any]:
    """Copia del preset `name`; un nombre desconocido es un error."""
    if name not in PRESETS:
        raise ValueError(f'unknown subtitle preset: {name}')
    return copy.deepcopy(PRESETS[name])


def ass_color(value: str) -> str:
    """Color `#RRGGBB` o `#RRGGBBAA` a `&HBBGGRR&` (o `&HAABBGGRR&` con opacidad) de ASS.

    >>> ass_color('#FFD400')
    '&H00D4FF&'
    >>> ass_color('#00000080')
    '&H7F000000&'
    """
    digits = value.lstrip('#')
    red, green, blue = digits[0:2], digits[2:4], digits[4:6]
    alpha = f'{255 - int(digits[6:8], 16):02X}' if len(digits) == 8 else ''
    return f'&H{alpha}{blue}{green}{red}&'.upper()
