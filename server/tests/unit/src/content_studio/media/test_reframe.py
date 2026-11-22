"""AC-4 (spec 015, D-3, T3): un video 16:9 pasa a Reels (1080×1920) con encuadre centrado, con barras y con
desenfoque. En las barras la franja de arriba es del color pedido; en el desenfoque no es de un solo color. Los cuadros
se leen con ffmpeg en rawvideo."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.media import convert

pytestmark = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
ENCODERS = frozenset({'libx264', 'aac'})
REELS = {'width': 1080, 'height': 1920}


def _source(tmp_path: Path) -> Path:
    """Un video 16:9 de 1920×1080 de un cuadro de colores (testsrc2) con tono."""
    path = tmp_path / 'wide.mp4'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            'testsrc2=size=1920x1080:rate=25:duration=1',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=330:duration=1',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-shortest',
            str(path),
        ],
        check=True,
    )
    return path


def _render(tmp_path: Path, reframe: dict) -> Path:
    """Convierte el video de 16:9 a Reels con el encuadre dado."""
    out = tmp_path / 'reels.mp4'
    convert.run(
        {'path': str(_source(tmp_path)), 'has_video': True},
        'mp4-h264',
        {**REELS, 'reframe': reframe},
        out,
        encoders=ENCODERS,
    )
    return out


def _first_frame_rgb(path: Path, width: int, height: int) -> bytes:
    """El primer cuadro como bytes RGB, sin decodificar a imagen."""
    return subprocess.run(
        [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-i',
            str(path),
            '-frames:v',
            '1',
            '-f',
            'rawvideo',
            '-pix_fmt',
            'rgb24',
            '-s',
            f'{width}x{height}',
            '-',
        ],
        capture_output=True,
        check=True,
    ).stdout


def _pixel(frame: bytes, width: int, x: int, y: int) -> tuple[int, int, int]:
    """El color del pixel (x, y) de un cuadro RGB."""
    at = (y * width + x) * 3
    return frame[at], frame[at + 1], frame[at + 2]


def _size(path: Path) -> tuple[int, int]:
    """El ancho y el alto del primer stream de video."""
    out = subprocess.run(
        [
            'ffprobe',
            '-v',
            'error',
            '-select_streams',
            'v:0',
            '-show_entries',
            'stream=width,height',
            '-of',
            'csv=p=0',
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    width, height = out.split(',')
    return int(width), int(height)


@pytest.mark.parametrize(
    'reframe', [{'mode': 'center'}, {'mode': 'fit-bars', 'color': 'red'}, {'mode': 'fit-blur', 'strength': 20}]
)
def test_ac4_reels_is_1080_by_1920_for_every_fixed_mode(tmp_path, reframe):
    """AC-4: centrado, barras y desenfoque dan 1080×1920."""
    assert _size(_render(tmp_path, reframe)) == (1080, 1920)


def test_ac4_bars_paint_the_top_strip_with_the_requested_color(tmp_path):
    """AC-4: con barras, la franja de arriba (fuera de la imagen 16:9) es del color pedido."""
    out = _render(tmp_path, {'mode': 'fit-bars', 'color': 'red'})
    assert _size(out) == (1080, 1920)

    red, green, blue = _pixel(_first_frame_rgb(out, 1080, 1920), 1080, 540, 2)
    assert red > 200 and green < 60 and blue < 60


def test_ac4_blur_fills_the_top_strip_with_more_than_one_color(tmp_path):
    """AC-4: con desenfoque, la franja de arriba es la imagen borrosa, no un color plano."""
    out = _render(tmp_path, {'mode': 'fit-blur', 'strength': 20})
    assert _size(out) == (1080, 1920)

    frame = _first_frame_rgb(out, 1080, 1920)
    row = {_pixel(frame, 1080, x, 2) for x in range(0, 1080, 20)}
    assert len(row) > 10
