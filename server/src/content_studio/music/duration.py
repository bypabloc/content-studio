"""Duración exacta de la música (spec 011, D-1): cuánto se le pide al motor y cómo se corta la pista a lo pedido."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from content_studio.music.evaluation import trim_silence

FADE_S = 2.0  # el fade de salida de una pista exacta
MARGIN = 0.25  # lo que se pide de más: el recorte del silencio final se come parte de la pista
MIN_EXTRA_S = 10  # y al menos esto de más, para las pistas cortas
TOLERANCE_S = 0.05  # una pista más corta que lo pedido por esto ya es corta (el corte deja ±10 ms)


def length(path: Path) -> float:
    """Duración del archivo en segundos (ffprobe)."""
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(out)


def write_result(output: Path, requested: float, duration: float) -> None:
    """Deja `<pista>.result.json` con lo pedido, lo que dura y el aviso `music_short` si salió corta."""
    warning = 'music_short' if duration < requested - TOLERANCE_S else None
    result = {'requested': requested, 'duration': round(duration, 3), 'warning': warning}
    output.with_suffix('.result.json').write_text(json.dumps(result), encoding='utf-8')


def plan_duration(target: float, engine_max: float) -> int:
    """Segundos que se le piden al motor para un objetivo: +25 %, con un mínimo de +10 s, sin pasar su máximo.

    >>> plan_duration(30, 600), plan_duration(60, 600), plan_duration(590, 600)
    (40, 75, 600)
    """
    return math.ceil(min(engine_max, max(target * (1 + MARGIN), target + MIN_EXTRA_S)))


def fade_for(target: float) -> float:
    """Largo del fade de salida: 2 s, o un tercio del objetivo si es menor de 6 s.

    >>> fade_for(30), fade_for(4)
    (2.0, 1.3333333333333333)
    """
    return FADE_S if target >= 6 else target / 3


def finish(path: Path, target: float) -> float:
    """Quita el silencio final; si la pista alcanza `target`, la deja en `target` con fade. Devuelve los segundos."""
    trimmed = trim_silence(path)
    if trimmed >= target:
        fit(path, target)
        return target
    return trimmed


def fit(path: Path, target: float) -> None:
    """Corta la pista en `target` segundos con un fade de salida, en el lugar. La pista ya debe durar `target` o más."""
    fade = fade_for(target)
    tmp = path.with_suffix('.fitted.wav')
    # Curva hsin (media sinusoide): el último medio segundo baja 23 dB. lin baja 17 y exp deja silencio digital.
    audio_filter = f'afade=t=out:st={target - fade}:d={fade}:curve=hsin'
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-t', str(target), '-af', audio_filter, tmp],
        check=True,
    )
    tmp.replace(path)
