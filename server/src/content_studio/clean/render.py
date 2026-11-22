"""Render del limpiador: audio y video sin los cortes, con crossfade entre tramos (spec 013, D-4).

Solo stdlib y ffmpeg.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from content_studio.common import ffmpeg as ff

# cspell:ignore acrossfade afade anull aout STARTPTS: filtros y etiquetas de ffmpeg, que el diccionario no trae.

FADE_SECONDS = 0.015  # crossfade entre tramos, y fade de los tramos de menos de 30 ms
SHORT_SEGMENT_SECONDS = 0.03


def _seconds(value: float) -> str:
    """Un tiempo en segundos sin ceros de sobra: 0.015, 1.15, 3."""
    return f'{value:.6f}'.rstrip('0').rstrip('.') or '0'


def audio_graph(keep: Sequence[tuple[float, float]]) -> str:
    """filter_complex de audio: un trim por tramo y un acrossfade entre tramos consecutivos.

    Un tramo de menos de 30 ms no se puede fundir con acrossfade; recibe afade de entrada y de salida de 15 ms.

    >>> print(audio_graph([(0.0, 1.0), (2.0, 3.0)]).rstrip())
    [0:a]atrim=start=0:end=1,asetpts=PTS-STARTPTS[a0];
    [0:a]atrim=start=2:end=3,asetpts=PTS-STARTPTS[a1];
    [a0][a1]acrossfade=d=0.015[x1];
    [x1]anull[aout]
    """
    fade = _seconds(FADE_SECONDS)
    chains: list[str] = []
    for index, (start, end) in enumerate(keep):
        duration = end - start
        fades = ''
        if duration < SHORT_SEGMENT_SECONDS:
            fades = f',afade=t=in:d={fade},afade=t=out:st={_seconds(duration - FADE_SECONDS)}:d={fade}'
        chains.append(f'[0:a]atrim=start={_seconds(start)}:end={_seconds(end)},asetpts=PTS-STARTPTS{fades}[a{index}]')
    current = 'a0'
    for index in range(1, len(keep)):
        label = f'x{index}'
        chains.append(f'[{current}][a{index}]acrossfade=d={fade}[{label}]')
        current = label
    chains.append(f'[{current}]anull[aout]')
    return ';\n'.join(chains) + '\n'


def render_audio(source: Path, keep: Sequence[tuple[float, float]], destination: Path) -> None:
    """Escribe en `destination` el audio de `source` solo con los tramos `keep`.

    El grafo va en un archivo (`-filter_complex_script`) para no pasar el límite de la línea de comandos de Windows.
    WAV sale en PCM de 24 bits; cualquier otro formato, en AAC a 192 kbps.
    """
    script = destination.parent / 'audio-filter.txt'
    script.write_text(audio_graph(keep), encoding='utf-8')
    codec = ['-c:a', 'pcm_s24le'] if destination.suffix.lower() == '.wav' else ['-c:a', 'aac', '-b:a', '192k']
    ff.ffmpeg(
        '-y', '-i', str(source), '-filter_complex_script', str(script), '-map', '[aout]', *codec, str(destination)
    )
