"""GET /media/info y /media/peaks: duración, LUFS y pico de un audio, y los picos de su forma de onda (spec 006, D-3).

Los números se guardan en memoria por (ruta, mtime, tamaño): si el archivo cambia, la clave cambia. El audio no
se manda al WebView; solo los números.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import APIRouter, Query, Request

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
        except subprocess.CalledProcessError as error:
            raise ApiError(422, 'unreadable_media') from error
    return _info[key]


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
