"""Render del limpiador: audio y video sin los cortes; cada tramo lleva un fundido de 15 ms y se une sin solaparse
(spec 013, D-4).

Solo stdlib y ffmpeg.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path

from content_studio.common import ffmpeg as ff
from content_studio.common.encode import video_codec

# cspell:ignore acrossfade afade anull aout vout STARTPTS setpts nvenc libx: filtros y codificadores de ffmpeg.

FADE_SECONDS = 0.015  # fundido de entrada y de salida de cada tramo, a cada lado de una unión


def frames_per_second(source: Path) -> float:
    """Tasa de cuadros del video como número: ffprobe da fracciones como «30000/1001»."""
    rate = ff.frame_rate(source)
    if '/' in rate:
        numerator, denominator = rate.split('/')
        return int(numerator) / int(denominator)
    return float(rate)


def _frame_index(seconds: float, fps: float) -> int:
    """El primer cuadro cuyo instante no es menor que `seconds`: así lo elige ffmpeg en `trim`. El redondeo a 6
    decimales quita el ruido de coma flotante (26.000000000000004 sería 27 si no)."""
    return math.ceil(round(seconds * fps, 6))


def on_frame_grid(keep: Sequence[tuple[float, float]], fps: float) -> list[tuple[float, float]]:
    """Cada tramo en los instantes de sus cuadros, como los corta `trim`. El audio se corta en esos mismos instantes,
    así su duración coincide con la del video (AC-11, sincronía) y el número de cuadros no cambia.

    >>> on_frame_grid([(0.61, 1.04), (2.0, 2.01)], 25)
    [(0.64, 1.04), (2.0, 2.04)]
    """
    snapped = [(_frame_index(start, fps) / fps, _frame_index(end, fps) / fps) for start, end in keep]
    return [(start, end) for start, end in snapped if end > start]


def _seconds(value: float) -> str:
    """Un tiempo en segundos sin ceros de sobra: 0.015, 1.15, 3."""
    return f'{value:.6f}'.rstrip('0').rstrip('.') or '0'


def _joined_audio_chains(keep: Sequence[tuple[float, float]]) -> list[str]:
    """Audio de cada tramo con su fundido de entrada y de salida de 15 ms, unidos con concat sin solaparse. Un crossfade
    le quitaría 15 ms por unión: el audio dejaría de durar lo que dice el informe y los subtítulos se desfasarían
    (AC-11, sincronía)."""
    fade = _seconds(FADE_SECONDS)
    chains: list[str] = []
    for index, (start, end) in enumerate(keep):
        fade_out = _seconds(max(0.0, end - start - FADE_SECONDS))
        chains.append(
            f'[0:a]atrim=start={_seconds(start)}:end={_seconds(end)},asetpts=PTS-STARTPTS,'
            f'afade=t=in:d={fade},afade=t=out:st={fade_out}:d={fade}[a{index}]'
        )
    labels = ''.join(f'[a{index}]' for index in range(len(keep)))
    chains.append(f'{labels}concat=n={len(keep)}:v=0:a=1[aout]')
    return chains


def _video_chains(keep: Sequence[tuple[float, float]]) -> list[str]:
    chains = [
        f'[0:v]trim=start={_seconds(start)}:end={_seconds(end)},setpts=PTS-STARTPTS[v{index}]'
        for index, (start, end) in enumerate(keep)
    ]
    labels = ''.join(f'[v{index}]' for index in range(len(keep)))
    chains.append(f'{labels}concat=n={len(keep)}:v=1:a=0[vout]')
    return chains


def audio_graph(keep: Sequence[tuple[float, float]]) -> str:
    """filter_complex de audio: un trim y un fundido de 15 ms por tramo, unidos con concat.

    >>> print(audio_graph([(0.0, 1.0), (2.0, 3.0)]).rstrip())
    [0:a]atrim=start=0:end=1,asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st=0.985:d=0.015[a0];
    [0:a]atrim=start=2:end=3,asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st=0.985:d=0.015[a1];
    [a0][a1]concat=n=2:v=0:a=1[aout]
    """
    return ';\n'.join(_joined_audio_chains(keep)) + '\n'


def video_graph(keep: Sequence[tuple[float, float]]) -> str:
    """filter_complex de video: un trim por tramo y un concat con todos.

    >>> print(video_graph([(0.0, 1.0), (2.0, 3.0)]).rstrip())
    [0:v]trim=start=0:end=1,setpts=PTS-STARTPTS[v0];
    [0:v]trim=start=2:end=3,setpts=PTS-STARTPTS[v1];
    [v0][v1]concat=n=2:v=1:a=0[vout]
    """
    return ';\n'.join(_video_chains(keep)) + '\n'


def _write_script(destination: Path, name: str, chains: list[str]) -> Path:
    """Escribe el grafo en un archivo: la línea de comandos de Windows tiene un límite corto."""
    script = destination.parent / name
    script.write_text(';\n'.join(chains) + '\n', encoding='utf-8')
    return script


def render_video(source: Path, keep: Sequence[tuple[float, float]], destination: Path, nvenc: bool) -> None:
    """Escribe en `destination` el video y el audio de `source` solo con los tramos `keep`."""
    keep = on_frame_grid(keep, frames_per_second(source))
    script = _write_script(destination, 'video-filter.txt', _video_chains(keep) + _joined_audio_chains(keep))
    ff.ffmpeg(
        '-y',
        '-i', str(source),
        '-/filter_complex', str(script),
        '-map', '[vout]',
        '-map', '[aout]',
        '-r', ff.frame_rate(source),  # sin esto, ffmpeg une los tramos a 25 cuadros por segundo
        *video_codec(nvenc),
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k',
        str(destination),
    )  # fmt: skip


def render_audio(source: Path, keep: Sequence[tuple[float, float]], destination: Path) -> None:
    """Escribe en `destination` el audio de `source` solo con los tramos `keep`.

    WAV sale en PCM de 24 bits; cualquier otro formato, en AAC a 192 kbps.
    """
    script = _write_script(destination, 'audio-filter.txt', _joined_audio_chains(keep))
    codec = ['-c:a', 'pcm_s24le'] if destination.suffix.lower() == '.wav' else ['-c:a', 'aac', '-b:a', '192k']
    ff.ffmpeg('-y', '-i', str(source), '-/filter_complex', str(script), '-map', '[aout]', *codec, str(destination))
