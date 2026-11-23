"""Render visual del lienzo del editor (spec 018, AC-4)."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import pytest

from content_studio.editor import project, render_video
from content_studio.media import convert, formats
from content_studio.system import tools

TRANSITIONS = ('fade', 'fadeblack', 'fadewhite', 'wipeleft', 'wiperight', 'slideleft', 'slideright', 'circleopen')


def test_video_quality_uses_crf_without_a_hardware_encoder(monkeypatch: pytest.MonkeyPatch):
    """Con CPU, la calidad elegida se pasa como CRF al codificador del formato."""
    monkeypatch.setattr(tools, 'detect', lambda: {'gpu': None})

    assert render_video._video_codec_args(formats.TARGETS['mp4-h264'], 21) == [
        '-c:v',
        'libx264',
        '-crf',
        '21',
        '-preset',
        'medium',
    ]


def test_video_quality_uses_cq_with_nvenc(monkeypatch: pytest.MonkeyPatch):
    """Con NVENC, la calidad elegida se pasa como CQ al codificador de NVIDIA."""
    monkeypatch.setattr(tools, 'detect', lambda: {'gpu': 'NVIDIA'})
    monkeypatch.setattr(convert, 'available_encoders', lambda: ['h264_nvenc'])

    assert render_video._video_codec_args(formats.TARGETS['mp4-h264'], 21) == [
        '-c:v',
        'h264_nvenc',
        '-preset',
        'p5',
        '-cq',
        '21',
    ]


@pytest.mark.parametrize('time', [-0.1, 0.1])
def test_render_frame_rejects_times_outside_the_document(tmp_path: Path, time: float):
    """Un instante negativo o después del proyecto no produce un cuadro falso."""
    doc = {'canvas': project.DEFAULT_CANVAS, 'clips': []}

    with pytest.raises(ValueError, match='unreadable_media'):
        render_video.render_frame(doc, tmp_path, time, tmp_path / 'frame.png')


def test_render_frame_writes_one_png_for_an_empty_canvas(tmp_path: Path):
    """Un proyecto sin clips muestra el fondo configurado en su lienzo."""
    if shutil.which('ffmpeg') is None:
        pytest.skip('FFmpeg no está en el PATH')
    output = tmp_path / 'frame.png'
    doc = {'canvas': project.DEFAULT_CANVAS, 'clips': []}

    render_video.render_frame(doc, tmp_path, 0, output)

    probe = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x', str(output)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert probe.stdout.strip() == '1920x1080'


def test_ac2_layer_keyframe_and_alpha_match_the_exported_frame(tmp_path: Path):
    """AC-2: x=200 a 1 s centra el rojo en 840 y conserva su alfa de 50 % sobre negro."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg no está en el PATH')
    logo = tmp_path / 'logo.png'
    subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'nullsrc=s=200x200:d=1,format=rgba,geq=r=255:g=0:b=0:a=128',
            '-frames:v',
            '1',
            '-c:v',
            'png',
            '-pix_fmt',
            'rgba',
            str(logo),
        ],
        capture_output=True,
        check=True,
    )
    canvas = {**project.DEFAULT_CANVAS, 'width': 1280, 'height': 720}
    doc = {
        'canvas': canvas,
        'tracks': [{'id': 'v1', 'kind': 'video'}],
        'clips': [
            {
                'id': 'logo',
                'track': 'v1',
                'src': 'logo.png',
                'media': 'image',
                'src_in': 0,
                'src_out': 2,
                'start': 0,
                'gain_db': 0,
                'fade_in': 0,
                'fade_out': 0,
                'transform': {
                    'x': 0,
                    'y': 0,
                    'scale_x': 1,
                    'scale_y': 1,
                    'rotation': 0,
                    'opacity': 1,
                    'anchor_x': 0.5,
                    'anchor_y': 0.5,
                    'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
                },
                'keyframes': {'x': [{'t': 0, 'value': 0, 'ease': 'linear'}, {'t': 2, 'value': 400, 'ease': 'linear'}]},
            }
        ],
    }
    output = tmp_path / 'frame.png'

    render_video.render_frame(doc, tmp_path, 1, output)

    raw = subprocess.run(
        [ffmpeg, '-v', 'error', '-i', str(output), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True,
        check=True,
    ).stdout
    center = raw[(360 * 1280 + 840) * 3 : (360 * 1280 + 840) * 3 + 3]
    old_center = raw[(360 * 1280 + 640) * 3 : (360 * 1280 + 640) * 3 + 3]
    assert abs(center[0] - 127) <= 3
    assert center[1:] == b'\x00\x00'
    assert old_center == b'\x00\x00\x00'


def test_build_graph_uses_segment_expressions_and_dynamic_alpha_masks(tmp_path: Path):
    """El grafo usa curvas por tramo, alfa para crop animado y tamaño evaluado por cuadro."""
    canvas = {**project.DEFAULT_CANVAS, 'width': 320, 'height': 240, 'fps': 10}
    doc = {
        'canvas': canvas,
        'tracks': [{'id': 'v1', 'kind': 'video', 'opacity': 0.5, 'hidden': False}],
        'clips': [
            {
                'id': 'clip',
                'track': 'v1',
                'src': 'logo.png',
                'media': 'image',
                'src_in': 0,
                'src_out': 2,
                'start': 0,
                'gain_db': 0,
                'fade_in': 0,
                'fade_out': 0,
                'transform': {
                    'x': 0,
                    'y': 0,
                    'scale_x': 1,
                    'scale_y': 1,
                    'rotation': 0,
                    'opacity': 1,
                    'anchor_x': 0.5,
                    'anchor_y': 0.5,
                    'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
                },
                'keyframes': {
                    'x': [
                        {'t': 0, 'value': 0, 'ease': 'linear'},
                        {'t': 1, 'value': 100, 'ease': 'ease-in-out'},
                        {'t': 2, 'value': 200, 'ease': 'linear'},
                    ],
                    'crop_l': [
                        {'t': 0, 'value': 0, 'ease': 'linear'},
                        {'t': 2, 'value': 0.25, 'ease': 'linear'},
                    ],
                    'scale_x': [
                        {'t': 0, 'value': 1, 'ease': 'linear'},
                        {'t': 2, 'value': 2, 'ease': 'linear'},
                    ],
                },
            }
        ],
    }

    plan = render_video.build(doc, tmp_path, source_sizes={(tmp_path / 'logo.png').resolve(): (200, 200)})

    assert 'geq=' in plan.script
    assert 'if(lt(t,1)' in plan.script
    assert 'scale=w=' in plan.script and ':eval=frame' in plan.script
    assert 'rotate=angle=' in plan.script
    assert 'overlay=' in plan.script and 'gte(t,0)*lt(t,2)' in plan.script


def test_build_graph_composes_tracks_in_array_order_and_skips_hidden_tracks(tmp_path: Path):
    """Las pistas visuales se apilan de abajo hacia arriba según su orden en el documento."""
    doc = {
        'canvas': {**project.DEFAULT_CANVAS, 'width': 320, 'height': 240},
        'tracks': [
            {'id': 'bottom', 'kind': 'video', 'opacity': 1, 'hidden': False},
            {'id': 'top', 'kind': 'video', 'opacity': 1, 'hidden': False},
            {'id': 'hidden', 'kind': 'video', 'opacity': 1, 'hidden': True},
        ],
        'clips': [
            {
                'id': track,
                'track': track,
                'src': f'{track}.png',
                'media': 'image',
                'src_in': 0,
                'src_out': 1,
                'start': 0,
                'gain_db': 0,
                'fade_in': 0,
                'fade_out': 0,
                'transform': {
                    'x': 0,
                    'y': 0,
                    'scale_x': 1,
                    'scale_y': 1,
                    'rotation': 0,
                    'opacity': 1,
                    'anchor_x': 0.5,
                    'anchor_y': 0.5,
                    'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
                },
                'keyframes': {},
            }
            for track in ('bottom', 'top', 'hidden')
        ],
    }

    sizes = {(tmp_path / f'{track}.png').resolve(): (100, 100) for track in ('bottom', 'top')}
    plan = render_video.build(doc, tmp_path, source_sizes=sizes)

    assert [item.path.name for item in plan.inputs] == ['bottom.png', 'top.png']
    assert plan.script.index('[1:v]') < plan.script.index('[2:v]')


def test_render_frame_applies_animated_crop_scale_rotation_and_track_opacity(tmp_path: Path):
    """Las máscaras y transformaciones animadas conservan alfa al componer sobre el lienzo."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg no está en el PATH')
    logo = tmp_path / 'logo.png'
    subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=red:s=100x100:d=1',
            '-frames:v',
            '1',
            '-c:v',
            'png',
            str(logo),
        ],
        capture_output=True,
        check=True,
    )
    canvas = {**project.DEFAULT_CANVAS, 'width': 640, 'height': 360, 'fps': 10}
    doc = {
        'canvas': canvas,
        'tracks': [{'id': 'v1', 'kind': 'video', 'opacity': 0.5, 'hidden': False}],
        'clips': [
            {
                'id': 'logo',
                'track': 'v1',
                'src': 'logo.png',
                'media': 'image',
                'src_in': 0,
                'src_out': 1,
                'start': 0,
                'gain_db': 0,
                'fade_in': 0,
                'fade_out': 0,
                'transform': {
                    'x': 0,
                    'y': 0,
                    'scale_x': 1,
                    'scale_y': 1,
                    'rotation': 0,
                    'opacity': 1,
                    'anchor_x': 0.5,
                    'anchor_y': 0.5,
                    'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
                },
                'keyframes': {
                    'crop_l': [{'t': 0, 'value': 0, 'ease': 'linear'}, {'t': 1, 'value': 0.25, 'ease': 'linear'}],
                    'rotation': [{'t': 0, 'value': 0, 'ease': 'linear'}, {'t': 1, 'value': 90, 'ease': 'linear'}],
                    'scale_x': [{'t': 0, 'value': 1, 'ease': 'linear'}, {'t': 1, 'value': 1.5, 'ease': 'linear'}],
                },
            }
        ],
    }
    output = tmp_path / 'animated.png'

    render_video.render_frame(doc, tmp_path, 0.5, output)

    raw = subprocess.run(
        [ffmpeg, '-v', 'error', '-i', str(output), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True,
        check=True,
    ).stdout
    center = raw[(180 * 640 + 320) * 3 : (180 * 640 + 320) * 3 + 3]
    assert abs(center[0] - 127) <= 3
    assert center[1:] == b'\x00\x00'


@pytest.mark.parametrize('transition', TRANSITIONS)
def test_transition_has_its_expected_pattern_in_the_exact_frame(tmp_path: Path, transition: str):
    """La transición cambia el cuadro dentro del solapamiento y conserva ambas imágenes."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg no está en el PATH')
    doc = _transition_project(tmp_path, transition)
    output = tmp_path / f'{transition}.png'

    render_video.render_frame(doc, tmp_path, 2.5, output)

    raw = subprocess.run(
        [ffmpeg, '-v', 'error', '-i', str(output), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True,
        check=True,
    ).stdout
    center = _pixel(raw, 128, 128)
    if transition == 'fade':
        assert abs(center[0] - 127) <= 4 and abs(center[2] - 127) <= 4
    elif transition == 'fadeblack':
        assert max(center) <= 100
    elif transition == 'fadewhite':
        assert min(center) >= 150
    elif transition == 'circleopen':
        assert center[2] >= 250 and _pixel(raw, 8, 8)[0] >= 250
    else:
        samples = [_pixel(raw, x, 128) for x in range(8, 257, 16)]
        assert any(red >= 250 and blue <= 5 for red, _, blue in samples)
        assert any(blue >= 250 and red <= 5 for red, _, blue in samples)


def test_transition_preserves_png_alpha_over_a_lower_track(tmp_path: Path):
    """Un fundido de imágenes transparentes conserva visible la pista inferior."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg no está en el PATH')
    doc = _transition_project(tmp_path, 'fade')
    for color in ('red', 'blue'):
        subprocess.run(
            [
                ffmpeg,
                '-v',
                'error',
                '-y',
                '-f',
                'lavfi',
                '-i',
                f'color={color}:s=256x256:d=1,format=rgba,colorchannelmixer=aa=0',
                '-frames:v',
                '1',
                '-c:v',
                'png',
                '-pix_fmt',
                'rgba',
                str(tmp_path / f'{color}.png'),
            ],
            capture_output=True,
            check=True,
        )
    subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=lime:s=256x256:d=1',
            '-frames:v',
            '1',
            '-c:v',
            'png',
            str(tmp_path / 'green.png'),
        ],
        capture_output=True,
        check=True,
    )
    doc['tracks'] = [
        {'id': 'v0', 'kind': 'video', 'opacity': 1, 'hidden': False},
        {'id': 'v1', 'kind': 'video', 'opacity': 1, 'hidden': False},
    ]
    for clip in doc['clips']:
        clip['track'] = 'v1'
    doc['transitions'][0]['track'] = 'v1'
    doc['clips'].append(
        {
            'id': 'green',
            'track': 'v0',
            'src': 'green.png',
            'media': 'image',
            'src_in': 0,
            'src_out': 5,
            'start': 0,
            'transform': doc['clips'][0]['transform'],
            'keyframes': {},
            'fade_in': 0,
            'fade_out': 0,
            'gain_db': 0,
        }
    )
    output = tmp_path / 'transparent-transition.png'

    render_video.render_frame(doc, tmp_path, 2.5, output)

    raw = subprocess.run(
        [ffmpeg, '-v', 'error', '-i', str(output), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True,
        check=True,
    ).stdout
    red, green, blue = _pixel(raw, 128, 128)
    assert red <= 5 and green >= 250 and blue <= 5


def test_ac3_fade_transition_last_five_seconds_and_keeps_the_average_color(tmp_path: Path):
    """AC-3: dos clips de 3 s con un segundo de solapamiento duran 5 s y funden ambos colores."""
    if shutil.which('ffmpeg') is None:
        pytest.skip('FFmpeg no está en el PATH')
    doc = _transition_project(tmp_path, 'fade')
    output = tmp_path / 'fade.mp4'

    render_video.render(doc, tmp_path, output, 'mp4-h264')

    assert ffmpeg_duration(output) == pytest.approx(5, abs=0.1)
    assert output.with_suffix('.filter').is_file()
    frame = tmp_path / 'fade-mid.png'
    subprocess.run(
        [shutil.which('ffmpeg'), '-v', 'error', '-y', '-ss', '2.5', '-i', str(output), '-frames:v', '1', str(frame)],
        capture_output=True,
        check=True,
    )
    raw = subprocess.run(
        [shutil.which('ffmpeg'), '-v', 'error', '-i', str(frame), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True,
        check=True,
    ).stdout
    center = _pixel(raw, 128, 128)
    assert abs(center[0] - 127) <= 4 and abs(center[2] - 127) <= 4


@pytest.mark.local
def test_ac6_renders_forty_clips_within_the_time_budget(tmp_path: Path):
    """AC-6: renderiza 40 clips con keyframes en 60 s dentro del presupuesto."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg no está en el PATH')
    source = tmp_path / 'source.png'
    subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=red:s=128x128:d=1',
            '-frames:v',
            '1',
            '-c:v',
            'png',
            str(source),
        ],
        capture_output=True,
        check=True,
    )
    transform = {
        'x': 0,
        'y': 0,
        'scale_x': 1,
        'scale_y': 1,
        'rotation': 0,
        'opacity': 1,
        'anchor_x': 0.5,
        'anchor_y': 0.5,
        'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
    }
    keyframes = {
        'x': [{'t': 0, 'value': 0, 'ease': 'linear'}, {'t': 1.5, 'value': 80, 'ease': 'linear'}],
        'scale_x': [{'t': 0, 'value': 1, 'ease': 'linear'}, {'t': 1.5, 'value': 1.2, 'ease': 'linear'}],
        'opacity': [{'t': 0, 'value': 1, 'ease': 'linear'}, {'t': 1.5, 'value': 0.8, 'ease': 'linear'}],
    }
    doc = {
        'canvas': {**project.DEFAULT_CANVAS, 'width': 1280, 'height': 720, 'fps': 30},
        'tracks': [{'id': 'v1', 'kind': 'video', 'opacity': 1, 'hidden': False}],
        'clips': [
            {
                'id': f'clip-{index}',
                'track': 'v1',
                'src': source.name,
                'media': 'image',
                'src_in': 0,
                'src_out': 1.5,
                'start': index * 1.5,
                'gain_db': 0,
                'fade_in': 0,
                'fade_out': 0,
                'transform': transform,
                'keyframes': keyframes if index < 20 else {},
            }
            for index in range(40)
        ],
    }
    output = tmp_path / 'ac6.mp4'
    started = time.perf_counter()

    render_video.render(doc, tmp_path, output, 'mp4-h264')

    elapsed = time.perf_counter() - started
    graph_size = output.with_suffix('.filter').stat().st_size
    nvenc = tools.detect()['gpu'] is not None and 'h264_nvenc' in convert.available_encoders()
    limit = (3 if nvenc else 6) * 60
    assert ffmpeg_duration(output) == pytest.approx(60, abs=0.1)
    assert graph_size > 0
    assert elapsed < limit


def _transition_project(folder: Path, transition: str) -> dict:
    """Proyecto mínimo de dos PNG que se solapan durante un segundo."""
    ffmpeg = shutil.which('ffmpeg')
    assert ffmpeg is not None
    for color in ('red', 'blue'):
        subprocess.run(
            [
                ffmpeg,
                '-v',
                'error',
                '-y',
                '-f',
                'lavfi',
                '-i',
                f'color={color}:s=256x256:d=1',
                '-frames:v',
                '1',
                '-c:v',
                'png',
                str(folder / f'{color}.png'),
            ],
            capture_output=True,
            check=True,
        )
    transform = {
        'x': 0,
        'y': 0,
        'scale_x': 1,
        'scale_y': 1,
        'rotation': 0,
        'opacity': 1,
        'anchor_x': 0.5,
        'anchor_y': 0.5,
        'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
    }
    return {
        'canvas': {**project.DEFAULT_CANVAS, 'width': 256, 'height': 256, 'fps': 10},
        'tracks': [{'id': 'v1', 'kind': 'video', 'opacity': 1, 'hidden': False}],
        'clips': [
            {
                'id': color,
                'track': 'v1',
                'src': f'{color}.png',
                'media': 'image',
                'src_in': 0,
                'src_out': 3,
                'start': start,
                'gain_db': 0,
                'fade_in': 0,
                'fade_out': 0,
                'transform': transform,
                'keyframes': {},
            }
            for color, start in (('red', 0), ('blue', 2))
        ],
        'transitions': [{'id': 'tr1', 'track': 'v1', 'a': 'red', 'b': 'blue', 'type': transition, 'duration': 1}],
    }


def _pixel(raw: bytes, x: int, y: int, width: int = 256) -> tuple[int, int, int]:
    index = (y * width + x) * 3
    return tuple(raw[index : index + 3])


def ffmpeg_duration(path: Path) -> float:
    """Duración del archivo, medida con ffprobe."""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout)
