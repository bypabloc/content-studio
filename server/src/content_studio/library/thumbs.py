"""Miniaturas de la biblioteca (spec 020, D-1): un cuadro JPEG al 10 % del video, en una caché de disco.

El nombre es el SHA-1 de la ruta y la fecha de cambio: si el archivo cambia, la miniatura es otra. Las imágenes se
reducen igual. La base no guarda imágenes; el audio se dibuja en el client con `/media/peaks`.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from content_studio import paths

WIDTH = 320  # ancho de la tarjeta de la grilla


def thumb_path(path: str, mtime: float) -> Path:
    """`<datos>/cache/thumbs/<sha1(path|mtime)>.jpg`."""
    digest = hashlib.sha1(f'{path}|{mtime}'.encode()).hexdigest()
    return paths.data_dir() / 'cache' / 'thumbs' / f'{digest}.jpg'


def thumbnail(item: dict) -> Path:
    """La miniatura del ítem (video o imagen), generada la primera vez. ValueError si no tiene o no se pudo sacar."""
    if item['media_type'] not in ('video', 'other'):
        raise ValueError('no thumbnail for this media type')
    target = thumb_path(item['path'], item['mtime'])
    if target.is_file() and target.stat().st_size:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    seek = ['-ss', f'{(item.get("duration") or 0) * 0.1:.3f}'] if item['media_type'] == 'video' else []
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *seek, '-i', item['path'],
               '-frames:v', '1', '-vf', f'scale={WIDTH}:-2', '-q:v', '4', str(target)]  # fmt: skip
    try:
        subprocess.run(command, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as error:
        target.unlink(missing_ok=True)
        raise ValueError('ffmpeg could not extract a frame') from error
    if not target.is_file() or not target.stat().st_size:
        target.unlink(missing_ok=True)
        raise ValueError('ffmpeg wrote no frame')
    return target
