"""Almacén de proyectos del editor (spec 017, D-1 y D-3): carpetas, `project.json` con su hash y escritura atómica.

Un proyecto es una carpeta `<AAAA-MM-DD>-<slug>/` con `project.json`, `media/` y `exports/`. El hash del contenido es
el `If-Match` de un guardado: si el archivo cambió desde que se leyó, el guardado se rechaza y no se escribe nada.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import unicodedata
import wave
from datetime import date
from pathlib import Path
from typing import Any

# cspell:ignore IHDR: identificador de bloque PNG.
from content_studio.editor.project import DEFAULT_CANVAS, SAMPLE_RATE, VERSION, Doc, migrate

FILE = 'project.json'
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
TEXT_RASTER_LIMIT = 16 * 1024 * 1024


class ProjectChanged(Exception):
    """El archivo cambió desde el hash que mandó el cliente (`If-Match`): el guardado no se hace."""

    def __init__(self, current: str) -> None:
        """Guarda el hash actual del archivo."""
        super().__init__(current)
        self.current = current


def slug(name: str) -> str:
    """El nombre en kebab-case ASCII: «Charla de prueba» da «charla-de-prueba»; vacío da «proyecto».

    >>> slug('Charla de prueba')
    'charla-de-prueba'
    """
    text = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-') or 'project'


def new_doc(name: str) -> Doc:
    """El documento vacío del esquema v3, con lienzo y una pista de audio."""
    track = {
        'id': 't1',
        'kind': 'audio',
        'name': 'Track 1',
        'volume_db': 0,
        'mute': False,
        'solo': False,
        'locked': False,
    }
    return {
        'version': VERSION,
        'name': name,
        'sample_rate': SAMPLE_RATE,
        'canvas': dict(DEFAULT_CANVAS),
        'tracks': [{**track, 'height': 80}],
        'clips': [],
        'markers': [],
        'transitions': [],
    }


def create(root: Path, name: str, today: date) -> Path:
    """Crea `root/<AAAA-MM-DD>-<slug>/` con `media/`, `exports/` y el `project.json`. Devuelve la ruta del archivo."""
    folder = root / f'{today.isoformat()}-{slug(name)}'
    number = 2
    while folder.exists():
        folder = root / f'{today.isoformat()}-{slug(name)}-{number}'
        number += 1
    (folder / 'media').mkdir(parents=True)
    (folder / 'exports').mkdir()
    path = folder / FILE
    path.write_bytes(serialize(new_doc(name)))
    return path


def unique_export_path(folder: Path, name: str, extension: str) -> Path:
    """Elige un nombre de exportación libre sin reemplazar salidas anteriores del proyecto."""
    base = slug(name)
    target = folder / f'{base}{extension}'
    number = 2
    while target.exists():
        target = folder / f'{base}-{number}{extension}'
        number += 1
    return target


def serialize(doc: Doc) -> bytes:
    """El JSON del proyecto, en UTF-8 y con un salto final: lo mismo siempre para el mismo documento."""
    return (json.dumps(doc, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def hash_of(data: bytes) -> str:
    """El hash del contenido del archivo: lo que el cliente devuelve en `If-Match`."""
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> tuple[Doc, str]:
    """El documento migrado al esquema actual y el hash original para `If-Match`."""
    data = path.read_bytes()
    doc: Doc = migrate(json.loads(data.decode('utf-8')))
    return doc, hash_of(data)


def write(path: Path, doc: Doc, expected: str) -> str:
    """Guarda `doc` si el archivo sigue con el hash `expected`; si no, `ProjectChanged` y el archivo queda igual.

    La escritura va a un temporal y entra con `os.replace`, así que nunca queda un `project.json` a medias.
    """
    current = hash_of(path.read_bytes())
    if current != expected:
        raise ProjectChanged(current)
    data = serialize(doc)
    temporary = path.with_name(f'{FILE}.tmp')
    temporary.write_bytes(data)
    os.replace(temporary, path)
    return hash_of(data)


def missing(folder: Path, doc: dict[str, Any]) -> list[str]:
    """Las fuentes de los clips que no existen en el disco, sin repetir. Una ruta relativa cuelga de la carpeta."""
    found: list[str] = []
    for clip in doc['clips']:
        source = Path(clip['src'])
        target = source if source.is_absolute() else folder / source
        if not target.exists() and clip['src'] not in found:
            found.append(clip['src'])
    return found


def save_recording(folder: Path, data: bytes) -> tuple[str, float]:
    """Valida y guarda una toma PCM mono de 24 bits y 48 kHz sin sobrescribir otra grabación."""
    try:
        with wave.open(io.BytesIO(data), 'rb') as recording:
            if (
                recording.getnchannels() != 1
                or recording.getsampwidth() != 3
                or recording.getframerate() != SAMPLE_RATE
                or recording.getnframes() <= 0
            ):
                raise ValueError('editor_recording_invalid')
            duration = recording.getnframes() / recording.getframerate()
    except (wave.Error, EOFError) as error:
        raise ValueError('editor_recording_invalid') from error

    media = folder / 'media'
    if not media.is_dir():
        raise ValueError('editor_recording_invalid')
    number = 1
    while True:
        relative = Path('media') / f'rec-{number:03}.wav'
        target = folder / relative
        try:
            with target.open('xb') as output:
                output.write(data)
        except FileExistsError:
            number += 1
            continue
        return relative.as_posix(), duration


def save_text_raster(folder: Path, data: bytes, clip_id: str, expected_hash: str) -> str:
    """Valida y guarda un PNG con alfa con nombre determinista dentro de `media/`."""
    if (
        len(data) > TEXT_RASTER_LIMIT
        or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', clip_id)
        or not re.fullmatch(r'[a-f0-9]{64}', expected_hash)
        or len(data) < 26
        or data[:8] != PNG_SIGNATURE
        or data[12:16] != b'IHDR'
    ):
        raise ValueError('editor_text_raster_invalid')
    width = int.from_bytes(data[16:20], 'big')
    height = int.from_bytes(data[20:24], 'big')
    color_type = data[25]
    digest = hashlib.sha256(data).hexdigest()
    if (
        width < 1
        or height < 1
        or width > 16384
        or height > 16384
        or color_type not in {4, 6}
        or digest != expected_hash
    ):
        raise ValueError('editor_text_raster_invalid')

    relative = Path('media') / f'text-{clip_id}-{digest}.png'
    media = folder / 'media'
    if not media.is_dir():
        raise ValueError('editor_text_raster_invalid')
    target = media / relative.name
    try:
        with target.open('xb') as output:
            output.write(data)
    except FileExistsError:
        if target.read_bytes() != data:
            raise ValueError('editor_text_raster_invalid') from None
    return relative.as_posix()
