"""GET /media/info y /media/peaks: duración, LUFS y pico de un audio, y los picos de su forma de onda (spec 006, D-3).

Los números se guardan en memoria por (ruta, mtime, tamaño): si el archivo cambia, la clave cambia. El audio no
se manda al WebView; solo los números.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse

from content_studio import paths
from content_studio.api.errors import ApiError
from content_studio.api.paths_guard import allowed_file
from content_studio.common import ffmpeg

router = APIRouter()
_info: dict[tuple, dict] = {}
_peaks: dict[tuple, list[float]] = {}


def _key(target: Path) -> tuple[str, int, int]:
    """Ruta, fecha de cambio y tamaño del archivo."""
    stat = target.stat()
    return str(target), stat.st_mtime_ns, stat.st_size


@router.get('/media/info')
def media_info(path: str, request: Request) -> dict:
    """Duración (s), LUFS integrado y pico real (dBTP) del audio."""
    target = allowed_file(request, path)
    key = _key(target)
    if key not in _info:
        try:
            lufs, true_peak = ffmpeg.loudness(target)
            _info[key] = {'duration': ffmpeg.probe_duration(target), 'lufs': lufs, 'true_peak': true_peak}
        except (subprocess.CalledProcessError, ValueError) as error:  # ValueError: ffmpeg no dio el resumen
            raise ApiError(422, 'unreadable_media') from error
    return _info[key]


@router.get('/media/frame')
def media_frame(path: str, request: Request, t: float = Query(0.0, ge=0)) -> FileResponse:
    """Un cuadro JPEG del video en el segundo `t`, para la vista previa del encuadre (spec 015, D-6).

    Se guarda en `outputs/tmp/frames/` por (ruta, mtime, tamaño, t): un cambio en el archivo da otro cuadro.
    """
    target = allowed_file(request, path)
    key = (*_key(target), round(t, 3))
    frame = paths.outputs_dir() / 'tmp' / 'frames' / f'{hashlib.sha1(repr(key).encode()).hexdigest()}.jpg'
    if not frame.is_file():
        frame.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(t), '-i', str(target),
                 '-frames:v', '1', '-q:v', '3', str(frame)],
                check=True,
            )  # fmt: skip
        except subprocess.CalledProcessError as error:
            raise ApiError(422, 'unreadable_media') from error
        if not frame.is_file() or frame.stat().st_size == 0:  # un instante después del final no tiene cuadro
            frame.unlink(missing_ok=True)
            raise ApiError(422, 'unreadable_media')
    return FileResponse(frame, media_type='image/jpeg')


@router.get('/media/peaks')
def media_peaks(path: str, request: Request, n: int = Query(2000, ge=1, le=5000)) -> dict:
    """`n` picos del audio, entre 0 y 1, para dibujar la forma de onda."""
    target = allowed_file(request, path)
    key = (*_key(target), n)
    if key not in _peaks:
        try:
            _peaks[key] = ffmpeg.peaks(target, n)
        except subprocess.CalledProcessError as error:
            raise ApiError(422, 'unreadable_media') from error
    return {'peaks': _peaks[key]}
