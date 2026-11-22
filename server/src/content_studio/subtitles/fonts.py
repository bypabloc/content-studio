"""Fuentes de Subtítulos (spec 014, D-6): las incluidas en `server/data/fonts` y las del sistema, sin fontTools.

La familia sale de la tabla `name` (nameID 16 o, si no, 1); el estilo, de 17 o, si no, 2. Se lee solo la tabla `name`.
"""

from __future__ import annotations

# cspell:ignore SFNT WINDIR LOCALAPPDATA
import os
import shutil
import struct
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import BinaryIO

FONT_SUFFIXES = ('.ttf', '.otf')
SFNT_VERSIONS = (b'\x00\x01\x00\x00', b'OTTO', b'true')  # TrueType, CFF y Apple
_SFNT_HEADER = struct.Struct('>4sHHHH')  # versión, número de tablas, y tres campos de búsqueda
_TABLE_RECORD = struct.Struct('>4sIII')  # etiqueta, suma de control, desplazamiento, longitud
_NAME_HEADER = struct.Struct('>HHH')  # formato, cantidad de registros, desplazamiento de los textos
_NAME_RECORD = struct.Struct('>HHHHHH')  # plataforma, codificación, idioma, nameID, longitud, desplazamiento


def _name_table(f: BinaryIO) -> bytes | None:
    """La tabla `name` del archivo, o None si no es una fuente SFNT."""
    head = f.read(_SFNT_HEADER.size)
    if len(head) < _SFNT_HEADER.size or head[:4] not in SFNT_VERSIONS:
        return None
    count = _SFNT_HEADER.unpack(head)[1]
    for _ in range(count):
        tag, _checksum, offset, length = _TABLE_RECORD.unpack(f.read(_TABLE_RECORD.size))
        if tag == b'name':
            f.seek(offset)
            return f.read(length)
    return None


def _names(table: bytes) -> dict[int, str]:
    """Los textos de la tabla por nameID; Windows (plataforma 3) gana a Mac (1) y el primero de cada uno cuenta."""
    _, count, string_offset = _NAME_HEADER.unpack_from(table, 0)
    records = [_NAME_RECORD.unpack_from(table, _NAME_HEADER.size + i * _NAME_RECORD.size) for i in range(count)]
    names: dict[int, str] = {}
    for platform, _encoding, _language, name_id, length, offset in sorted(records, key=lambda r: r[0] != 3):
        if platform not in (1, 3):
            continue
        start = string_offset + offset
        codec = 'utf-16-be' if platform == 3 else 'latin-1'
        names.setdefault(name_id, table[start : start + length].decode(codec, errors='replace').strip())
    return names


def read_names(path: Path) -> tuple[str, str] | None:
    """(familia, estilo) de una fuente, o None si el archivo no es una fuente legible."""
    try:
        with path.open('rb') as f:
            table = _name_table(f)
        names = _names(table) if table is not None else {}
    except (OSError, struct.error):
        return None
    family = names.get(16) or names.get(1)
    if not family:
        return None
    return family, names.get(17) or names.get(2) or 'Regular'


def _font_files(folder: Path) -> list[Path]:
    """Los archivos de fuente bajo una carpeta, ordenados; una carpeta que no existe no tiene ninguno."""
    if not folder.is_dir():
        return []
    return sorted(path for path in folder.rglob('*') if path.suffix.lower() in FONT_SUFFIXES and path.is_file())


def list_fonts(bundled_dir: Path, system_files: Iterable[Path]) -> list[dict]:
    """Familias con sus estilos y un archivo (el Regular si hay). Las incluidas van primero; `bundled` las marca."""
    grouped: dict[tuple[str, bool], dict] = {}
    sources = [(True, path) for path in _font_files(bundled_dir)] + [(False, path) for path in system_files]
    for bundled, path in sources:
        names = read_names(path)
        if names is None:
            continue
        family, style = names
        entry = grouped.setdefault(
            (family, bundled), {'family': family, 'styles': [], 'path': str(path), 'bundled': bundled}
        )
        if style not in entry['styles']:
            entry['styles'].append(style)
        if style == 'Regular':
            entry['path'] = str(path)
    for entry in grouped.values():
        entry['styles'].sort()
    return sorted(grouped.values(), key=lambda entry: (not entry['bundled'], entry['family'].lower()))


def system_font_dirs(env: Mapping[str, str] = os.environ) -> list[Path]:
    """Las carpetas de fuentes de Windows: la del sistema y la del usuario (si LOCALAPPDATA existe)."""
    dirs = [Path(env.get('WINDIR', 'C:\\Windows')) / 'Fonts']
    if 'LOCALAPPDATA' in env:
        dirs.append(Path(env['LOCALAPPDATA']) / 'Microsoft' / 'Windows' / 'Fonts')
    return dirs


def font_roots(bundled: Path, platform: str = sys.platform, env: Mapping[str, str] = os.environ) -> list[Path]:
    """Las carpetas de fuentes que /files puede servir: la incluida y, en Windows, las del sistema."""
    folders = [bundled, *(system_font_dirs(env) if platform == 'win32' else [])]
    return [folder.resolve() for folder in folders]


def system_font_files(env: Mapping[str, str] = os.environ, platform: str = sys.platform) -> list[Path]:
    """Las fuentes instaladas: las carpetas de Windows, o lo que lista `fc-list` en POSIX."""
    if platform == 'win32':
        return [path for folder in system_font_dirs(env) for path in _font_files(folder)]
    if shutil.which('fc-list') is None:
        return []
    listing = subprocess.run(['fc-list', '--format=%{file}\n'], capture_output=True, text=True, check=False)
    return [Path(line) for line in listing.stdout.splitlines() if line.strip()]
