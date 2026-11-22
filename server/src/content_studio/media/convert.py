"""Armador de comandos de conversión (spec 015, D-1): los argumentos de ffmpeg de cada formato. Solo stdlib.

`build` no tiene una clase por formato: lee el catálogo de `media/formats.py` y arma los argumentos. No pone la ruta de
salida (la pone quien llama), así `build` es puro y se prueba con argumentos golden.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from content_studio.common.encode import video_codec
from content_studio.common.ffmpeg import probe_duration
from content_studio.media.formats import TARGETS
from content_studio.media.reframe import graph as reframe_graph

_PCM = {16: 'pcm_s16le', 24: 'pcm_s24le', 32: 'pcm_f32le'}
_OPUS_RATES = frozenset({8000, 12000, 16000, 24000, 48000})  # libopus no codifica otras frecuencias


class ConvertError(ValueError):
    """Un error del armador: su código (que el catálogo traduce) y sus parámetros."""

    def __init__(self, code: str, **params: Any) -> None:
        """El código del error y los parámetros de su texto."""
        super().__init__(code)
        self.code = code
        self.params = params


def build(input_info: dict[str, Any], target: str, options: dict[str, Any], encoders: frozenset[str]) -> list[str]:
    """Argumentos de ffmpeg para convertir `input_info` al formato `target`, sin la ruta de salida.

    `encoders` son los códecs que trae el ffmpeg del sistema (`system.detect()`); uno que falta da `codec_unavailable`.
    """
    spec = TARGETS.get(target)
    if spec is None or spec['kind'] == 'gif':
        raise ConvertError('unknown_target', target=target)
    args = ['-y', '-i', input_info['path']]
    if spec['kind'] == 'audio':
        name, codec_args = _audio_args(target, options)
        needed = [name]
        rate = options.get('sample_rate')
        if target == 'ogg-opus' and rate is not None and rate not in _OPUS_RATES:
            raise ConvertError('sample_rate_unsupported', codec='libopus', rate=rate)
        if input_info.get('has_video'):
            args.append('-vn')
    else:
        name, codec_args = _video_args(spec, options, encoders)
        audio = _video_audio(spec)
        codec_args = codec_args + audio
        needed = [name, audio[1]]
        if 'reframe' in options:
            graph = reframe_graph(options['reframe'], options['width'], options['height'])
            args += ['-filter_complex', graph, '-map', '[v]', '-map', '0:a?']
        else:
            filters = _video_filters(options)
            if filters:
                args += ['-vf', ','.join(filters)]
    missing = [codec for codec in needed if codec not in encoders]
    if missing:
        raise ConvertError('codec_unavailable', codec=missing[0])
    return args + codec_args + _mix_args(options)


def _video_filters(options: dict[str, Any]) -> list[str]:
    """Filtros de video: la altura (manteniendo el aspecto) y la tasa de cuadros, si se pidieron."""
    filters: list[str] = []
    if 'resolution' in options:
        filters.append(f'scale=-2:{options["resolution"]}')
    if 'fps' in options:
        filters.append(f'fps={options["fps"]}')
    return filters


def gif_passes(input_info: dict[str, Any], output: Path, options: dict[str, Any]) -> list[list[str]]:
    """Las dos pasadas de un GIF: la paleta (`palettegen`) y el GIF con ella (`paletteuse`, dither sierra2_4a).

    La paleta va junto a la salida, en `<salida>.palette.png`; quien llama la borra al terminar.
    """
    fps = options.get('fps', 15)
    width = options.get('width', 480)
    palette = output.with_name(output.name + '.palette.png')
    scale = f'fps={fps},scale={width}:-1:flags=lanczos'
    first = ['-y', '-i', input_info['path'], '-vf', f'{scale},palettegen=stats_mode=diff', str(palette)]
    second = [
        '-y',
        '-i',
        input_info['path'],
        '-i',
        str(palette),
        '-an',
        '-lavfi',
        f'{scale}[x];[x][1:v]paletteuse=dither=sierra2_4a',
        str(output),
    ]
    return [first, second]


def run(
    input_info: dict[str, Any],
    target: str,
    options: dict[str, Any],
    output: Path,
    *,
    encoders: frozenset[str],
    on_progress: Callable[[float], None] | None = None,
) -> None:
    """Convierte `input_info` a `output` con ffmpeg. Avisa el avance (0 a 1) con `on_progress` si lo pide.

    Un fallo de ffmpeg da `ffmpeg_failed` con el final de su salida de error.
    """
    if target == 'gif':
        if 'gif' not in encoders:
            raise ConvertError('codec_unavailable', codec='gif')
        passes = gif_passes(input_info, output, options)
    else:
        passes = [build(input_info, target, options, encoders) + [str(output)]]
    duration = probe_duration(input_info['path']) if on_progress is not None else 0.0
    try:
        for args in passes:
            _ffmpeg_with_progress(args, duration, on_progress)
    finally:
        if target == 'gif':
            output.with_name(output.name + '.palette.png').unlink(missing_ok=True)


def _ffmpeg_with_progress(args: list[str], duration: float, on_progress: Callable[[float], None] | None) -> None:
    """Corre ffmpeg con `-progress pipe:1` y avisa el avance por `out_time_us` (ffmpeg lo llama *_ms)."""
    proc = subprocess.Popen(
        ['ffmpeg', '-hide_banner', '-nostats', '-loglevel', 'error', '-progress', 'pipe:1', *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        if on_progress is not None and duration > 0 and line.startswith('out_time_ms='):
            value = line.split('=', 1)[1].strip()
            if value.isdigit():
                on_progress(min(1.0, int(value) / 1_000_000 / duration))
    stderr = proc.stderr.read() if proc.stderr is not None else ''
    if proc.wait() != 0:
        raise ConvertError('ffmpeg_failed', detail=stderr[-400:])


def _audio_args(target: str, options: dict[str, Any]) -> tuple[str, list[str]]:
    """El códec de audio y sus argumentos (calidad o tasa, y profundidad en WAV)."""
    if target == 'mp3':
        if 'bitrate' in options:
            return 'libmp3lame', ['-c:a', 'libmp3lame', '-b:a', f'{options["bitrate"]}k']
        return 'libmp3lame', ['-c:a', 'libmp3lame', '-q:a', str(options.get('vbr', 2))]
    if target == 'wav':
        codec = _PCM[options.get('depth', 16)]
        return codec, ['-c:a', codec]
    if target == 'flac':
        return 'flac', ['-c:a', 'flac', '-compression_level', str(options.get('level', 5))]
    if target == 'ogg-opus':
        return 'libopus', ['-c:a', 'libopus', '-b:a', f'{options.get("bitrate", 128)}k']
    if target == 'ogg-vorbis':
        return 'libvorbis', ['-c:a', 'libvorbis', '-q:a', str(options.get('quality', 5))]
    return 'aac', ['-c:a', 'aac', '-b:a', f'{options.get("bitrate", 192)}k']


def _video_args(spec: dict[str, Any], options: dict[str, Any], encoders: frozenset[str]) -> tuple[str, list[str]]:
    """El códec de video: NVENC si el ffmpeg lo trae y no se pide otra cosa; si no, el libx264 compartido."""
    if spec['codec'] == 'libx264':
        nvenc = spec['nvenc'] in encoders and options.get('nvenc', True)
        return (spec['nvenc'] if nvenc else 'libx264'), video_codec(bool(nvenc))
    return spec['codec'], ['-c:v', spec['codec']]


def _video_audio(spec: dict[str, Any]) -> list[str]:
    """El audio de un video: Opus en WebM; AAC en los demás contenedores."""
    if spec['ext'] == '.webm':
        return ['-c:a', 'libopus', '-b:a', '128k']
    return ['-c:a', 'aac', '-b:a', '192k']


def _mix_args(options: dict[str, Any]) -> list[str]:
    """Canales y frecuencia, si se pidieron (van después del códec)."""
    args: list[str] = []
    if 'channels' in options:
        args += ['-ac', str(options['channels'])]
    if 'sample_rate' in options:
        args += ['-ar', str(options['sample_rate'])]
    return args
