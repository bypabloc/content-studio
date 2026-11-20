"""`tracks.json`: lo que se muestra al comparar las pistas de un trabajo (spec 011, D-6), una fila por pista.

La duración real, el aviso `music_short`, la voz (null si no se evaluó), el LUFS, la tonalidad y el BPM salen de la
pista ya terminada. La elección («Elegir») se guarda aquí también, en `chosen`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from content_studio.common import ffmpeg
from content_studio.music.duration import TOLERANCE_S, length

MANIFEST = 'tracks.json'
_VARIANT = re.compile(r'-v(\d+)$')


def write_manifest(
    folder: Path,
    model: str,
    requested: float,
    tracks: list[tuple[dict, Path]],
    voices: dict[Path, bool],
) -> Path:
    """Escribe `tracks.json`; `voices` trae la voz de cada pista (vacío si no hubo evaluación).

    >>> _VARIANT.search('lofi-chill-v2').group(1)
    '2'
    """
    rows = []
    for style, output in tracks:
        seconds = length(output)
        stem = output.stem.removeprefix(f'{model}-')
        variant = _VARIANT.search(stem)
        rows.append(
            {
                'file': output.name,
                'style': _VARIANT.sub('', stem),
                'variant': int(variant.group(1)) if variant else 1,
                'requested': requested,
                'duration': round(seconds, 3),
                'warning': 'music_short' if seconds < requested - TOLERANCE_S else None,
                'voice': voices.get(output),
                'lufs': round(ffmpeg.loudness(output)[0], 1),
                'key': style.get('key'),
                'bpm': style.get('bpm'),
            }
        )
    path = folder / MANIFEST
    path.write_text(json.dumps({'tracks': rows, 'chosen': None}, ensure_ascii=False, indent=2), encoding='utf-8')
    return path
