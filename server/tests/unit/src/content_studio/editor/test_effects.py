"""Filtros de color, LUT, chroma y fusión del Editor (spec 019, AC-3 y AC-5)."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

from content_studio.editor import effects, project, render_video
from content_studio.subtitles.burn import filter_path

FIXTURES = Path(__file__).resolve().parents[4] / 'fixtures' / 'editor'


def test_clip_filters_follow_color_lut_and_chroma_order(tmp_path: Path):
    """D-4: color, LUT y chroma se aplican en ese orden y el LUT queda dentro del proyecto."""
    relative = 'media/luts/lut-' + 'a' * 64 + '.cube'
    lut = tmp_path / relative
    lut.parent.mkdir(parents=True)
    lut.write_text('LUT_3D_SIZE 2\n', encoding='utf-8')
    clip = {
        'color': {'brightness': 0.2, 'contrast': 1.5, 'saturation': 0.7, 'gamma': 1.2, 'lut': relative},
        'chroma': {'color': '#00ff00', 'similarity': 0.2, 'blend': 0.1, 'despill': True},
    }

    filters = effects.clip_filters(clip, tmp_path)

    assert filters == [
        'eq=brightness=0.2:contrast=1.5:saturation=0.7:gamma=1.2',
        f'lut3d=file={filter_path(lut)}:interp=tetrahedral',
        'chromakey=0x00ff00:similarity=0.2:blend=0.1',
        'despill=type=green',
    ]


def test_blend_graph_uses_the_layer_alpha_mask():
    """D-4: la máscara alfa limita el modo de fusión antes de componer la capa."""
    lines, output = effects.blend_graph(
        'base', 'clip', 'multiply', {'width': 8, 'height': 4, 'fps': 24}, 2, '0', '0', 'gte(t,0)', '3'
    )

    assert output == 'v3'
    assert any('blend=all_mode=multiply' in line for line in lines)
    assert any('[b3_source_alpha]alphaextract[b3_mask]' in line for line in lines)
    assert any('[base]split=2[b3_background][b3_composite]' in line for line in lines)
    assert any('[b3_composite][b3_alpha]overlay=' in line for line in lines)


def test_blend_graph_maps_add_to_ffmpeg_addition():
    """D-4: el modo aditivo usa el nombre reconocido por FFmpeg."""
    lines, _ = effects.blend_graph(
        'base', 'clip', 'add', {'width': 8, 'height': 4, 'fps': 24}, 2, '0', '0', 'gte(t,0)', '3'
    )

    assert any('blend=all_mode=addition' in line for line in lines)


def test_save_lut_validates_cube_and_uses_a_content_hash(tmp_path: Path):
    """Una LUT 3D válida se escribe en media/luts y su nombre identifica el contenido."""
    data = b'LUT_3D_SIZE 2\n' + b'0 0 0\n' * 8
    (tmp_path / 'media').mkdir()

    relative = effects.save_lut(tmp_path, data)

    assert relative == f'media/luts/lut-{hashlib.sha256(data).hexdigest()}.cube'
    assert (tmp_path / relative).read_bytes() == data


@pytest.mark.parametrize(
    'data',
    [b'', b'LUT_1D_SIZE 2\n', b'LUT_3D_SIZE 2\n0 0 0\n', b'LUT_3D_SIZE 2\n' + b'2 0 0\n' * 8],
)
def test_save_lut_rejects_invalid_cube(tmp_path: Path, data: bytes):
    """No se guarda un archivo vacío ni una LUT con declaración o cantidad de puntos inválida."""
    (tmp_path / 'media').mkdir()

    with pytest.raises(ValueError, match='editor_lut_invalid'):
        effects.save_lut(tmp_path, data)


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
def test_render_chroma_replaces_green_and_preserves_red_subject(tmp_path: Path):
    """AC-5: chroma deja ver el fondo azul y conserva el sujeto rojo del cuadro."""
    source = tmp_path / 'green.ppm'
    pixels = [(0, 255, 0)] * 16
    for y in (1, 2):
        for x in (1, 2):
            pixels[y * 4 + x] = (255, 0, 0)
    _write_ppm(source, 4, 4, pixels)
    doc = _image_doc(source, background='#0000ff')
    doc['clips'][0]['chroma'] = {'color': '#00ff00', 'similarity': 0.2, 'blend': 0.1}

    frame = _render(doc, tmp_path)
    pixels = _pixels(frame)

    assert _pixel(pixels, 4, 0, 0) == pytest.approx((0, 0, 255), abs=4)
    assert _pixel(pixels, 4, 1, 1) == pytest.approx((255, 0, 0), abs=4)


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
def test_render_multiply_blend_matches_gray_over_white(tmp_path: Path):
    """AC-5: multiply de gris al 50 % sobre blanco da gris al 50 %."""
    source = tmp_path / 'gray.ppm'
    _write_ppm(source, 4, 4, [(128, 128, 128)] * 16)
    doc = _image_doc(source, background='#ffffff')
    doc['clips'][0]['blend_mode'] = 'multiply'

    frame = _render(doc, tmp_path)
    pixels = _pixels(frame)

    assert _pixel(pixels, 4, 2, 2) == pytest.approx((128, 128, 128), abs=4)


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
def test_render_multiply_keeps_transparent_pixels_of_the_layer(tmp_path: Path):
    """AC-5: el modo multiply no cubre el fondo donde la capa tiene alfa cero."""
    source = tmp_path / 'gray-alpha.png'
    rgba = [(0, 0, 0, 0)] * 16
    for y in (1, 2):
        for x in (1, 2):
            rgba[y * 4 + x] = (128, 128, 128, 255)
    _write_png_rgba(source, 4, 4, rgba)
    doc = _image_doc(source, background='#ffffff')
    doc['clips'][0]['blend_mode'] = 'multiply'

    frame = _render(doc, tmp_path)
    pixels = _pixels(frame)

    assert _pixel(pixels, 4, 0, 0) == pytest.approx((255, 255, 255), abs=4)
    assert _pixel(pixels, 4, 1, 1) == pytest.approx((128, 128, 128), abs=4)


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
def test_render_add_saturates_white(tmp_path: Path):
    """AC-5: la suma de canales que supera 255 se limita a blanco."""
    base = tmp_path / 'base.ppm'
    source = tmp_path / 'source.ppm'
    _write_ppm(base, 4, 4, [(220, 220, 220)] * 16)
    _write_ppm(source, 4, 4, [(100, 100, 100)] * 16)
    doc = _blend_doc(base, source, 'add')

    pixels = _pixels(_render(doc, tmp_path))

    assert _pixel(pixels, 4, 2, 2) == pytest.approx((255, 255, 255), abs=4)


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
def test_render_multiply_preserves_the_composite_under_the_blended_clip(tmp_path: Path):
    """AC-5: una fusión en la capa superior conserva el chroma y fondo ya compuestos."""
    fixture = json.loads((FIXTURES / 'parity-effects.json').read_text(encoding='utf-8'))
    doc = fixture['doc']
    next(clip for clip in doc['clips'] if clip['id'] == 'blend')['blend_mode'] = 'multiply'
    frame = tmp_path / 'frame.png'

    render_video.render_frame(doc, FIXTURES, 0.5, frame)
    pixels = _pixels(frame)

    assert _pixel(pixels, 800, 0, 0) == pytest.approx((31, 80, 127), abs=4)
    assert _pixel(pixels, 800, 200, 225) == pytest.approx((253, 30, 30), abs=6)


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
def test_render_identity_lut_preserves_the_source_pixel(tmp_path: Path):
    """AC-3: una LUT 3D de identidad conserva el color de la imagen."""
    source = tmp_path / 'identity.ppm'
    _write_ppm(source, 4, 4, [(128, 64, 32)] * 16)
    doc = _image_doc(source, background='#000000')
    (tmp_path / 'media').mkdir()
    doc['clips'][0]['color']['lut'] = effects.save_lut(tmp_path, _identity_cube())

    pixels = _pixels(_render(doc, tmp_path))

    assert _pixel(pixels, 4, 2, 2) == pytest.approx((128, 64, 32), abs=4)


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
def test_render_contrast_lut_uses_the_3d_samples(tmp_path: Path):
    """AC-3: una LUT 3D de contraste transforma el gris medio al nivel de la muestra central."""
    source = tmp_path / 'contrast.ppm'
    _write_ppm(source, 4, 4, [(128, 128, 128)] * 16)
    doc = _image_doc(source, background='#000000')
    (tmp_path / 'media').mkdir()
    doc['clips'][0]['color']['lut'] = effects.save_lut(tmp_path, _contrast_cube())

    pixels = _pixels(_render(doc, tmp_path))

    assert _pixel(pixels, 4, 2, 2) == pytest.approx((64, 64, 64), abs=4)


def _image_doc(source: Path, *, background: str) -> dict:
    """Crea un proyecto v3 mínimo con una imagen de pantalla completa."""
    raw = json.loads((FIXTURES / 'valid-visual-v2.json').read_text(encoding='utf-8'))['doc']
    doc = project.migrate(raw)
    clip = next(clip for clip in doc['clips'] if clip.get('media') == 'video')
    clip.update(media='image', src=source.as_posix(), src_in=0, src_out=1, start=0)
    clip.pop('link', None)
    clip['color'] = {'brightness': 0, 'contrast': 1, 'saturation': 1, 'gamma': 1}
    doc['clips'] = [clip]
    doc['tracks'] = [track for track in doc['tracks'] if track['id'] == clip['track']]
    doc['transitions'] = []
    doc['canvas'] = {**doc['canvas'], 'width': 4, 'height': 4, 'fps': 1, 'background': background}
    return doc


def _blend_doc(base: Path, source: Path, mode: str) -> dict:
    """Crea dos pistas de imagen con el modo indicado en la capa superior."""
    doc = _image_doc(base, background='#000000')
    top = dict(doc['clips'][0], id='top', track='top', src=source.as_posix(), blend_mode=mode)
    top['transform'] = dict(top['transform'])
    doc['clips'].append(top)
    doc['tracks'].append(
        {'id': 'top', 'kind': 'video', 'name': 'Superior', 'opacity': 1, 'hidden': False, 'locked': False}
    )
    return doc


def _render(doc: dict, folder: Path) -> Path:
    """Renderiza un cuadro con el FFmpeg instalado y devuelve el PNG."""
    frame = folder / 'frame.png'
    render_video.render_frame(doc, folder, 0, frame)
    return frame


def _pixels(frame: Path) -> bytes:
    """Decodifica el fotograma como RGBA para comparar los píxeles del resultado real."""
    return subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(frame), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
        check=True,
        capture_output=True,
    ).stdout


def _pixel(data: bytes, width: int, x: int, y: int) -> tuple[int, int, int]:
    """Lee un píxel RGB por sus coordenadas de origen superior izquierdo."""
    offset = (y * width + x) * 4
    return tuple(data[offset : offset + 3])


def _write_ppm(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    """Escribe una imagen PPM pequeña sin requerir otra biblioteca gráfica."""
    data = b''.join(bytes(pixel) for pixel in pixels)
    path.write_bytes(f'P6\n{width} {height}\n255\n'.encode('ascii') + data)


def _identity_cube() -> bytes:
    """Genera una LUT 3D de identidad de 2³ muestras con rojo como eje más rápido."""
    return b'LUT_3D_SIZE 2\n' + b''.join(
        f'{red} {green} {blue}\n'.encode('ascii') for blue in (0, 1) for green in (0, 1) for red in (0, 1)
    )


def _contrast_cube() -> bytes:
    """Genera una curva de contraste 3D con nivel central 0,25."""
    levels = (0, 0.25, 1)
    rows = (
        f'{levels[red]} {levels[green]} {levels[blue]}\n'.encode('ascii')
        for blue in range(3)
        for green in range(3)
        for red in range(3)
    )
    return b'LUT_3D_SIZE 3\n' + b''.join(rows)


def _write_png_rgba(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    """Escribe un PNG RGBA fixture con alfa para las pruebas del compositor."""
    rows = b''.join(
        b'\0' + b''.join(bytes(pixel) for pixel in pixels[y * width : (y + 1) * width]) for y in range(height)
    )

    def chunk(name: bytes, data: bytes) -> bytes:
        content = name + data
        return struct.pack('>I', len(data)) + content + struct.pack('>I', zlib.crc32(content))

    header = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')
    )
