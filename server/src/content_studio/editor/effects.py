"""Filtros de color y archivos LUT 3D del Editor (spec 019, D-4)."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path, PurePosixPath
from typing import Any

from content_studio.editor.schema import valid_chroma, valid_color
from content_studio.subtitles.burn import filter_path

LUT_LIMIT = 8 * 1024 * 1024
LUT_SIZE_LIMIT = 64


def clip_filters(clip: dict[str, Any], folder: Path) -> list[str]:
    """Devuelve los filtros del clip en orden de color, LUT y chroma."""
    filters: list[str] = []
    color = clip.get('color')
    if color is not None:
        if not valid_color(color):
            raise ValueError('editor_effect_invalid')
        if any(
            color[key] != default
            for key, default in (('brightness', 0), ('contrast', 1), ('saturation', 1), ('gamma', 1))
        ):
            filters.append(
                'eq='
                + ':'.join(f'{key}={_number(color[key])}' for key in ('brightness', 'contrast', 'saturation', 'gamma'))
            )
        if color.get('lut'):
            path = resolve_lut(folder, color['lut'])
            if not path.is_file():
                raise ValueError('editor_lut_invalid')
            filters.append(f'lut3d=file={filter_path(path)}:interp=tetrahedral')
    chroma = clip.get('chroma')
    if chroma is not None:
        if not valid_chroma(chroma) or ('despill' in chroma and not isinstance(chroma['despill'], bool)):
            raise ValueError('editor_effect_invalid')
        filters.append(
            f'chromakey=0x{chroma["color"][1:].lower()}:similarity={_number(chroma["similarity"])}:'
            f'blend={_number(chroma["blend"])}'
        )
        if chroma.get('despill'):
            red, green, blue = (int(chroma['color'][index : index + 2], 16) for index in (1, 3, 5))
            if max(green, blue) > red:
                filters.append(f'despill=type={"green" if green >= blue else "blue"}')
    return filters


def save_lut(folder: Path, data: bytes) -> str:
    """Valida una LUT `.cube` 3D y la guarda en `media/luts/` con hash de contenido."""
    if len(data) > LUT_LIMIT or not _valid_cube(data):
        raise ValueError('editor_lut_invalid')
    media = folder / 'media'
    if not media.is_dir():
        raise ValueError('editor_lut_invalid')
    digest = hashlib.sha256(data).hexdigest()
    relative = f'media/luts/lut-{digest}.cube'
    target = folder / relative
    target.parent.mkdir(exist_ok=True)
    if not target.resolve().is_relative_to(media.resolve()):
        raise ValueError('editor_lut_invalid')
    try:
        with target.open('xb') as output:
            output.write(data)
    except FileExistsError:
        if target.read_bytes() != data:
            raise ValueError('editor_lut_invalid') from None
    return relative


def blend_graph(
    current: str,
    source: str,
    mode: str,
    canvas: dict[str, Any],
    duration: float,
    x: str,
    y: str,
    enable: str,
    suffix: str,
) -> tuple[list[str], str]:
    """Compone una capa en modo normal o usa su alfa para un modo de fusión."""
    output = f'v{suffix}'
    if mode == 'normal':
        return [
            f'[{current}][{source}]overlay=x={x}:y={y}:'
            f"eval=frame:format=auto:alpha=straight:eof_action=pass:repeatlast=0:enable='{enable}'[{output}]"
        ], output
    ffmpeg_mode = 'addition' if mode == 'add' else mode
    blank, layer, blended, alpha, background, source_color, source_alpha = (
        f'b{suffix}_{name}' for name in ('blank', 'layer', 'blended', 'alpha', 'background', 'color', 'source_alpha')
    )
    size = f'{canvas["width"]}x{canvas["height"]}'
    fps = _number(canvas['fps'])
    length = _number(duration)
    lines = [
        f'color=c=black:s={size}:r={fps}:d={length},format=rgba,colorchannelmixer=aa=0[{blank}]',
        f'[{blank}][{source}]overlay=x={x}:y={y}:eval=frame:format=auto:alpha=straight:'
        f"eof_action=pass:repeatlast=0:enable='{enable}',format=rgba[{layer}]",
        f'[{layer}]split=2[{source_color}][{source_alpha}]',
        f'[{current}]split=2[{background}][b{suffix}_composite]',
        f'[{background}][{source_color}]blend=all_mode={ffmpeg_mode}:shortest=1,format=rgba[{blended}]',
        f'[{source_alpha}]alphaextract[b{suffix}_mask]',
        f'[{blended}][b{suffix}_mask]alphamerge[{alpha}]',
        f'[b{suffix}_composite][{alpha}]overlay=x=0:y=0:eval=frame:format=auto:alpha=straight:'
        f'eof_action=pass:repeatlast=0[{output}]',
    ]
    return lines, output


def resolve_lut(folder: Path, value: str) -> Path:
    """Resuelve solo archivos LUT generados dentro de `media/luts/`."""
    path = PurePosixPath(value)
    if (
        len(path.parts) != 3
        or path.parts[:2] != ('media', 'luts')
        or not path.name.startswith('lut-')
        or not path.name.endswith('.cube')
    ):
        raise ValueError('editor_lut_invalid')
    digest = path.name[4:-5]
    if len(digest) != 64 or any(char not in '0123456789abcdef' for char in digest):
        raise ValueError('editor_lut_invalid')
    resolved = (folder / Path(*path.parts)).resolve()
    media = (folder / 'media').resolve()
    luts = (folder / 'media' / 'luts').resolve()
    if (
        not media.is_relative_to(folder.resolve())
        or not luts.is_relative_to(media)
        or not resolved.is_relative_to(luts)
    ):
        raise ValueError('editor_lut_invalid')
    return resolved


def _valid_cube(data: bytes) -> bool:
    """Comprueba una declaración LUT_3D_SIZE y exactamente sus tripletas RGB."""
    try:
        lines = data.decode('utf-8-sig').splitlines()
    except UnicodeDecodeError:
        return False
    size = None
    rows = 0
    for raw in lines:
        line = raw.split('#', maxsplit=1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts[0] == 'TITLE':
            continue
        if parts[0] == 'LUT_3D_SIZE' and size is None and len(parts) == 2:
            try:
                size = int(parts[1])
            except ValueError:
                return False
            if not 2 <= size <= LUT_SIZE_LIMIT:
                return False
            continue
        if parts[0] in {'DOMAIN_MIN', 'DOMAIN_MAX'} and len(parts) == 4:
            if not all(_finite(part) for part in parts[1:]):
                return False
            continue
        if len(parts) != 3 or size is None or not all(_unit_interval(part) for part in parts):
            return False
        rows += 1
        if rows > size**3:
            return False
    return size is not None and rows == size**3


def _finite(value: str) -> bool:
    """Acepta un componente RGB numérico y finito."""
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def _unit_interval(value: str) -> bool:
    """Limita muestras RGB al rango que representa la vista previa de 8 bits."""
    try:
        number = float(value)
        return math.isfinite(number) and 0 <= number <= 1
    except ValueError:
        return False


def _number(value: float) -> str:
    """Representa un parámetro FFmpeg sin ceros finales innecesarios."""
    return format(float(value), '.12g')
