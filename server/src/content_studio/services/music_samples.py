"""Servicio `music.samples` de la cola (spec 011, D-3): las muestras de 10 s que faltan, con el candado de la GPU."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.music.styles import STYLES

RESOURCE = 'gpu'  # ACE-Step usa la GPU: una muestra detrás de otra, con el candado


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}: cada estilo pedido tiene que ser un preset."""
    return [
        {'code': 'unknown_style', 'params': {'style': style}}
        for style in params.get('styles', [])
        if style not in STYLES
    ]


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `music.samples_main`. Sin `styles`, hace todos los presets; con `force`, regenera."""
    args = ['--styles', *params['styles']] if 'styles' in params else []
    if params.get('force'):
        args.append('--force')
    return [sys.executable, '-m', 'content_studio.music.samples_main', *args]
