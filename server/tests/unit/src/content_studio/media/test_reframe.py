"""AC-4 (spec 015, D-3, T3): un video 16:9 pasa a Reels (1080×1920) con encuadre centrado, con barras y con
desenfoque. En las barras la franja de arriba es del color pedido; en el desenfoque no es de un solo color. Los cuadros
se leen con ffmpeg en rawvideo."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.media import convert, reframe

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


def test_crop_width_keeps_the_output_aspect_and_is_even():
    """El recorte de 9:16 de una fuente de 1080 de alto mide 608 px (par, con la proporción de salida)."""
    assert reframe.crop_width(source_height=1080, width=1080, height=1920) == 608


def test_crop_xs_centers_the_crop_on_the_face_and_keeps_it_inside_the_frame():
    """AC-5: la esquina del recorte queda centrada en la cara, en par, y nunca se sale del cuadro."""
    assert reframe.crop_xs([0.25, 0.75, 0.0, 1.0], source_width=1920, crop_w=608) == [176, 1136, 0, 1312]


def test_sendcmd_moves_the_crop_every_fifth_of_a_second():
    """AC-5: una orden `crop x` por muestra, cada 1/5 s."""
    script = reframe.sendcmd_script([176, 1136], fps=5)

    assert script.splitlines() == ['0.000000 crop x 176;', '0.200000 crop x 1136;']


def test_follow_face_graph_names_the_commands_file_with_colons_escaped():
    """El grafo de `follow-face` lee las órdenes de `sendcmd` (con los dos puntos de Windows escapados)."""
    graph = reframe.graph({'mode': 'follow-face', 'commands': 'C:/x/follow.txt', 'crop_w': 608}, 1080, 1920)

    assert graph == "[0:v]sendcmd=f='C\\:/x/follow.txt',crop=w=608:h=ih:x=0:y=0,scale=1080:1920[v]"


def test_follow_options_writes_the_crop_commands_from_the_track(tmp_path):
    """AC-5: el seguimiento (track.json) pasa a ser el modo `follow-face`: órdenes y ancho del recorte."""
    track = {'fps': 5.0, 'width': 1920, 'height': 1080, 'centers': [0.25, 0.75]}

    options = reframe.follow_options(track, 1080, 1920, tmp_path)

    assert options == {'mode': 'follow-face', 'commands': str(tmp_path / 'follow.txt'), 'crop_w': 608}
    commands = (tmp_path / 'follow.txt').read_text(encoding='utf-8').splitlines()
    assert commands == ['0.000000 crop x 176;', '0.200000 crop x 1136;']


def _halves(tmp_path: Path) -> Path:
    """Un video de 1 s: la mitad izquierda roja y la derecha azul (1920×1080, 25 cuadros por segundo)."""
    path = tmp_path / 'halves.mp4'
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
            'color=c=red:s=960x1080:r=25:d=1',
            '-f',
            'lavfi',
            '-i',
            'color=c=blue:s=960x1080:r=25:d=1',
            '-filter_complex',
            'hstack',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            str(path),
        ],
        check=True,
    )
    return path


def _pixel_at(path: Path, seconds: float) -> tuple[int, int, int]:
    """El color del centro del cuadro de 1080×1920 que cae en `seconds`."""
    frame = subprocess.run(
        [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-ss',
            str(seconds),
            '-i',
            str(path),
            '-frames:v',
            '1',
            '-f',
            'rawvideo',
            '-pix_fmt',
            'rgb24',
            '-s',
            '1080x1920',
            '-',
        ],
        capture_output=True,
        check=True,
    ).stdout
    return _pixel(frame, 1080, 540, 960)


def test_ac5_follow_face_moves_the_crop_with_the_commands(tmp_path):
    """AC-5: el recorte sigue las órdenes de `sendcmd`: al principio toma la mitad roja y, desde 0,8 s, la azul."""
    commands = tmp_path / 'follow.txt'
    commands.write_text(reframe.sendcmd_script([0, 0, 0, 0, 1312], fps=5), encoding='utf-8')
    out = tmp_path / 'reels.mp4'
    convert.run(
        {'path': str(_halves(tmp_path)), 'has_video': True},
        'mp4-h264',
        {**REELS, 'reframe': {'mode': 'follow-face', 'commands': str(commands), 'crop_w': 608}},
        out,
        encoders=ENCODERS,
    )

    red, _, blue = _pixel_at(out, 0.1)
    assert red > 200 and blue < 60
    red, _, blue = _pixel_at(out, 0.9)
    assert blue > 200 and red < 60
