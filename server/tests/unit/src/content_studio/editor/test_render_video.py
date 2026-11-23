"""Render visual del lienzo del editor (spec 018, AC-4)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.editor import project, render_video


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
