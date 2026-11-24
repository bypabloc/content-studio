"""Servicio de recortar (spec 015, D-5): valida el tramo y arma el comando de `content_studio.media.edit trim`.

Es ffmpeg: no carga modelos, así que la cola no toma el candado de la GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.media import edit

RESOURCE = 'cpu'  # es ffmpeg: no carga modelos, así que no toma el candado de la GPU


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}; vacío si el tramo puede correr. Contra la duración se mide en el job."""
    start, end = params.get('start'), params.get('end')
    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or start < 0 or end <= start:
        return [{'code': 'invalid_cut', 'params': {}}]
    fade_in, fade_out = params.get('fade_in', 0.0), params.get('fade_out', 0.0)
    if min(fade_in, fade_out) < 0 or fade_in + fade_out > end - start:
        return [{'code': 'invalid_cut', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando de `content_studio.media.edit trim`: el video sale en MP4 y el audio en WAV, en el trabajo."""
    source = Path(params['input'])
    out = output_dir / ('cut.mp4' if edit.has_video(source) else 'cut.wav')
    return [
        sys.executable,
        '-m',
        'content_studio.media.edit',
        'trim',
        '--input',
        str(source),
        '--out',
        str(out),
        '--start',
        str(params['start']),
        '--end',
        str(params['end']),
        '--mode',
        params.get('mode', 'keep'),
        '--fade-in',
        str(params.get('fade_in', 0.0)),
        '--fade-out',
        str(params.get('fade_out', 0.0)),
    ]
