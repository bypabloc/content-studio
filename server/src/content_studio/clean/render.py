"""Render del limpiador: audio y video sin los cortes, con crossfade entre tramos (spec 013, D-4).

Solo stdlib y ffmpeg.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from content_studio.common import ffmpeg as ff

# cspell:ignore acrossfade afade anull aout vout STARTPTS setpts nvenc libx: filtros y codificadores de ffmpeg.

FADE_SECONDS = 0.015  # crossfade entre tramos, y fade de los tramos de menos de 30 ms
SHORT_SEGMENT_SECONDS = 0.03


def _seconds(value: float) -> str:
    """Un tiempo en segundos sin ceros de sobra: 0.015, 1.15, 3."""
    return f'{value:.6f}'.rstrip('0').rstrip('.') or '0'


def _audio_chains(keep: Sequence[tuple[float, float]]) -> list[str]:
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
    """filter_complex de audio: un trim por tramo y un acrossfade entre tramos consecutivos.

    Un tramo de menos de 30 ms no se puede fundir con acrossfade; recibe afade de entrada y de salida de 15 ms.

    >>> print(audio_graph([(0.0, 1.0), (2.0, 3.0)]).rstrip())
    [0:a]atrim=start=0:end=1,asetpts=PTS-STARTPTS[a0];
    [0:a]atrim=start=2:end=3,asetpts=PTS-STARTPTS[a1];
    [a0][a1]acrossfade=d=0.015[x1];
    [x1]anull[aout]
    """
    return ';\n'.join(_audio_chains(keep)) + '\n'


def video_graph(keep: Sequence[tuple[float, float]]) -> str:
    """filter_complex de video: un trim por tramo y un concat con todos.

    >>> print(video_graph([(0.0, 1.0), (2.0, 3.0)]).rstrip())
    [0:v]trim=start=0:end=1,setpts=PTS-STARTPTS[v0];
    [0:v]trim=start=2:end=3,setpts=PTS-STARTPTS[v1];
    [v0][v1]concat=n=2:v=1:a=0[vout]
    """
    return ';\n'.join(_video_chains(keep)) + '\n'


def video_codec(nvenc: bool) -> list[str]:
    """Codificador de video: NVENC si el equipo tiene NVIDIA; si no, libx264 con CRF 18.

    >>> video_codec(nvenc=False)
    ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
    """
    if nvenc:
        return ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '19']
    return ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']


def _write_script(destination: Path, name: str, chains: list[str]) -> Path:
    """Escribe el grafo en un archivo: la línea de comandos de Windows tiene un límite corto."""
    script = destination.parent / name
    script.write_text(';\n'.join(chains) + '\n', encoding='utf-8')
    return script


def render_video(source: Path, keep: Sequence[tuple[float, float]], destination: Path, nvenc: bool) -> None:
    """Escribe en `destination` el video y el audio de `source` solo con los tramos `keep`."""
    script = _write_script(destination, 'video-filter.txt', _video_chains(keep) + _audio_chains(keep))
    ff.ffmpeg(
        '-y',
        '-i', str(source),
        '-filter_complex_script', str(script),
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
    script = _write_script(destination, 'audio-filter.txt', _audio_chains(keep))
    codec = ['-c:a', 'pcm_s24le'] if destination.suffix.lower() == '.wav' else ['-c:a', 'aac', '-b:a', '192k']
    ff.ffmpeg(
        '-y', '-i', str(source), '-filter_complex_script', str(script), '-map', '[aout]', *codec, str(destination)
    )
