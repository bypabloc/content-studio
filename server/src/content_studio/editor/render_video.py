"""Base del render visual del editor (spec 018): fotograma exacto del lienzo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from content_studio.common import ffmpeg
from content_studio.editor import project

# cspell:ignore lavfi: dispositivo de entrada sintÃ©tico de FFmpeg.


def render_frame(doc: dict[str, Any], folder: Path, time: float, output: Path) -> Path:
    """Escribe el cuadro del lienzo en `time`; T3 agrega las capas sobre el mismo render."""
    if time < 0 or time > project.duration(doc):
        raise ValueError('unreadable_media')
    canvas = doc['canvas']
    duration = max(project.duration(doc), 1 / canvas['fps'])
    source = f'color=c={canvas["background"]}:s={canvas["width"]}x{canvas["height"]}:r={canvas["fps"]}:d={duration}'
    ffmpeg.ffmpeg(
        '-y',
        '-f',
        'lavfi',
        '-i',
        source,
        '-ss',
        str(time),
        '-frames:v',
        '1',
        '-c:v',
        'png',
        '-f',
        'image2',
        str(output),
    )
    if not output.is_file() or not output.stat().st_size:
        raise ValueError('unreadable_media')
    return output
