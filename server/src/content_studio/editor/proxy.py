"""Proxies de video del editor (spec 018, D-3): caché por identidad de fuente, 540p y GOP corto."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from content_studio.common.encode import video_codec
from content_studio.media.formats import is_video

# cspell:ignore yuva pixfmt gbrap bgra argb abgr libvpx keyint: formatos, cÃ³decs y opciones de FFmpeg.


def cache_key(source: Path) -> str:
    """Hash estable de la ruta resuelta, mtime y tamaño de la fuente."""
    target = source.resolve()
    stat = target.stat()
    identity = f'{target}\0{stat.st_mtime_ns}\0{stat.st_size}'
    return hashlib.sha256(identity.encode('utf-8')).hexdigest()


def cache_path(source: Path, project_folder: Path, *, has_alpha: bool = False) -> Path:
    """Ruta del proxy dentro de la caché del proyecto, sin crear archivos."""
    extension = '.webm' if has_alpha else '.mp4'
    return project_folder / '.cache' / 'proxies' / f'{cache_key(source)}{extension}'


def create(source: Path, project_folder: Path) -> Path:
    """Crea el proxy de la fuente de video o devuelve el ya guardado en caché."""
    source = source.resolve()
    if not source.is_file() or not is_video(source):
        raise ValueError('unreadable_media')
    has_alpha = _has_alpha(source)
    target = cache_path(source, project_folder, has_alpha=has_alpha)
    if target.is_file() and target.stat().st_size:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f'.{target.stem}.{uuid4().hex}.tmp{target.suffix}')
    try:
        subprocess.run(_command(source, temporary, has_alpha), check=True, capture_output=True)
        if not temporary.is_file() or not temporary.stat().st_size:
            raise ValueError('unreadable_media')
        os.replace(temporary, target)
    except subprocess.CalledProcessError as error:
        raise ValueError('unreadable_media') from error
    finally:
        temporary.unlink(missing_ok=True)
    return target


def _has_alpha(source: Path) -> bool:
    """Detecta alfa por pix_fmt o `alpha_mode` del contenedor VP9."""
    result = subprocess.run(
        [
            'ffprobe',
            '-v',
            'error',
            '-select_streams',
            'v:0',
            '-show_entries',
            'stream=pix_fmt:stream_tags=alpha_mode',
            '-of',
            'json',
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(result.stdout).get('streams', [])
    if not streams:
        raise ValueError('unreadable_media')
    stream = streams[0]
    pixel_format = str(stream.get('pix_fmt', '')).lower()
    tags = {str(key).lower(): str(value).lower() for key, value in stream.get('tags', {}).items()}
    return (
        tags.get('alpha_mode') in {'1', 'true'}
        or pixel_format.startswith(('yuva', 'gbrap'))
        or pixel_format in {'rgba', 'bgra', 'argb', 'abgr', 'ya8', 'ya16be', 'ya16le', 'gray8a', 'gray16a'}
    )


def _command(source: Path, target: Path, has_alpha: bool) -> list[str]:
    """Comando ffmpeg del proxy: 540 píxeles de alto y un keyframe cada 15 cuadros."""
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
    if has_alpha:
        command += ['-c:v', 'libvpx-vp9']
    command += ['-i', str(source), '-map', '0:v:0', '-vf', 'scale=-2:540:flags=fast_bilinear', '-an', '-g', '15']
    if has_alpha:
        command += [
            '-c:v',
            'libvpx-vp9',
            '-pix_fmt',
            'yuva420p',
            '-auto-alt-ref',
            '0',
            '-crf',
            '33',
            '-b:v',
            '0',
            '-metadata:s:v:0',
            'alpha_mode=1',
        ]
    else:
        command += [*video_codec(nvenc=False), '-keyint_min', '15', '-sc_threshold', '0', '-pix_fmt', 'yuv420p']
    return [*command, str(target)]


def main(argv: list[str] | None = None) -> int:
    """CLI del worker: acepta el proyecto y la fuente que se van a cachear."""
    parser = argparse.ArgumentParser(description='Proxy visual para el editor')
    parser.add_argument('--project', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args(argv)
    source = Path(args.source)
    if not source.is_absolute():
        source = Path(args.project).resolve().parent / source
    try:
        result = create(source, Path(args.project).resolve().parent)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return 3
    print(result)
    return 0


if __name__ == '__main__':
    sys.exit(main())
