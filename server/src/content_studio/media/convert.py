"""Armador de comandos de conversión (spec 015, D-1): los argumentos de ffmpeg de cada formato. Solo stdlib.

`build` no tiene una clase por formato: lee el catálogo de `media/formats.py` y arma los argumentos. No pone la ruta de
salida (la pone quien llama), así `build` es puro y se prueba con argumentos golden.
"""

from __future__ import annotations

from typing import Any

from content_studio.common.encode import video_codec
from content_studio.media.formats import TARGETS

_PCM = {16: 'pcm_s16le', 24: 'pcm_s24le', 32: 'pcm_f32le'}


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
    if spec is None:
        raise ConvertError('unknown_target', target=target)
    if spec['kind'] == 'audio':
        name, codec_args = _audio_args(target, options)
        needed = [name]
    else:
        name, codec_args = _video_args(spec, options, encoders)
        audio = _video_audio(spec)
        codec_args = codec_args + audio
        needed = [name, audio[1]]
    missing = [codec for codec in needed if codec not in encoders]
    if missing:
        raise ConvertError('codec_unavailable', codec=missing[0])
    args = ['-y', '-i', input_info['path']]
    if spec['kind'] == 'audio' and input_info.get('has_video'):
        args.append('-vn')
    return args + codec_args + _mix_args(options)


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
