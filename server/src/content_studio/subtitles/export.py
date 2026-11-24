"""Exportar un documento de subtítulos a SRT, VTT o ASS (spec 014, D-3). Funciones puras.

El ASS usa el estilo del documento sobre el clásico y un PlayRes de 1920×1080; la quema usa la resolución real.
"""

from __future__ import annotations

from typing import Any

from content_studio.subtitles.ass import to_ass
from content_studio.subtitles.formats import to_srt, to_vtt
from content_studio.subtitles.styles import preset

FORMATS = ('srt', 'vtt', 'ass')


def render(document: dict[str, Any], fmt: str, play_res: tuple[int, int] = (1920, 1080)) -> str:
    """El texto del documento en el formato pedido; un formato que no existe es un ValueError."""
    if fmt == 'srt':
        return to_srt(document)
    if fmt == 'vtt':
        return to_vtt(document)
    if fmt == 'ass':
        return to_ass(document, {**preset('classic'), **document.get('style', {})}, play_res)
    raise ValueError(f'unknown export format: {fmt}')
