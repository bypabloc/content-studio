r"""Quemar los subtítulos en el video con ffmpeg y libass (spec 014, D-7; AC-6 y AC-7).

El filtro `subtitles` lee el ASS del trabajo y las fuentes de `fontsdir`; el audio se copia tal cual.
"""

from __future__ import annotations

from pathlib import Path

from content_studio.common import ffmpeg as ff
from content_studio.common.encode import video_codec


def filter_path(path: str | Path) -> str:
    r"""Una ruta como valor de una opción del filtro: `\` pasa a `/`, `:` y `'` se escapan y el valor va entre comillas.

    >>> filter_path(r'C:\Mis videos\sub.ass')
    "'C\\:/Mis videos/sub.ass'"
    """
    escaped = str(path).replace('\\', '/').replace(':', '\\:').replace("'", "\\'")
    return f"'{escaped}'"


def filter_value(ass: Path, fonts_dir: Path) -> str:
    """La expresión `subtitles` que comparte la quema directa y el Editor."""
    return f'subtitles=filename={filter_path(ass)}:fontsdir={filter_path(fonts_dir)}'


def burn_args(video: Path, ass: Path, fonts_dir: Path, destination: Path, *, nvenc: bool) -> list[str]:
    """Argumentos de ffmpeg: el filtro `subtitles` con sus fuentes, el codificador del equipo y el audio copiado."""
    return [
        '-y',
        '-i',
        str(video),
        '-vf',
        filter_value(ass, fonts_dir),
        *video_codec(nvenc),
        '-pix_fmt',
        'yuv420p',
        '-c:a',
        'copy',
        str(destination),
    ]


def burn(video: Path, ass: Path, fonts_dir: Path, destination: Path, *, nvenc: bool) -> None:
    """Escribe en `destination` el video con los subtítulos de `ass`; falla si ffmpeg falla (p. ej., sin libass)."""
    ff.ffmpeg(*burn_args(video, ass, fonts_dir, destination, nvenc=nvenc))
