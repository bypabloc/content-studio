"""Proxies de video del editor visual (spec 018, D-3 y AC-4)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.editor import proxy
from content_studio.services.registry import SERVICES


def test_ac4_proxy_job_is_registered():
    """Al importar un video, el worker puede encolar el servicio `editor.proxy`."""
    assert 'editor.proxy' in SERVICES


def test_ac4_cache_key_changes_with_source_size(tmp_path: Path):
    """La caché se invalida cuando cambia el tamaño de la fuente."""
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'one')

    first = proxy.cache_key(source)
    source.write_bytes(b'two!')
    second = proxy.cache_key(source)

    assert first != second


@pytest.fixture
def media_tools(monkeypatch):
    """FFmpeg y ffprobe reales para medir resolución, GOP y alfa."""
    if shutil.which('ffmpeg') is None or shutil.which('ffprobe') is None:
        pytest.skip('FFmpeg y ffprobe no están en el PATH')
    return 'ffmpeg', 'ffprobe'


def _probe(ffprobe: str, source: Path) -> dict:
    result = subprocess.run(
        [ffprobe, '-v', 'error', '-show_streams', '-show_frames', '-select_streams', 'v:0', '-of', 'json', str(source)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_ac4_proxy_has_540p_height_and_a_keyframe_every_15_frames(tmp_path: Path, media_tools):
    """El proxy H.264 conserva el tamaño de búsqueda rápida esperado por la línea de tiempo."""
    ffmpeg, ffprobe = media_tools
    source = tmp_path / '1080p.mp4'
    subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=blue:s=1920x1080:r=30:d=0.6',
            '-frames:v',
            '18',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            str(source),
        ],
        capture_output=True,
        check=True,
    )

    result = proxy.create(source, tmp_path / 'project')

    metadata = _probe(ffprobe, result)
    stream = metadata['streams'][0]
    keyframes = [index for index, frame in enumerate(metadata['frames']) if frame['key_frame'] == 1]
    assert (stream['width'], stream['height'], stream['codec_name']) == (960, 540, 'h264')
    assert keyframes == [0, 15]
    assert proxy.create(source, tmp_path / 'project') == result


def test_ac4_alpha_source_uses_vp9_webm_and_keeps_alpha(tmp_path: Path, media_tools):
    """Un video VP9 con `alpha_mode` conserva transparencia en el proxy WebM."""
    ffmpeg, ffprobe = media_tools
    source = tmp_path / 'alpha.webm'
    generated = subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'nullsrc=s=64x64:r=10:d=0.5,format=rgba,geq=r=255:g=0:b=0:a=128',
            '-frames:v',
            '5',
            '-c:v',
            'libvpx-vp9',
            '-pix_fmt',
            'yuva420p',
            '-auto-alt-ref',
            '0',
            '-metadata:s:v:0',
            'alpha_mode=1',
            str(source),
        ],
        capture_output=True,
        check=False,
    )
    if generated.returncode:
        pytest.skip('FFmpeg no admite codificación VP9 con alfa')

    result = proxy.create(source, tmp_path / 'project')

    stream = _probe(ffprobe, result)['streams'][0]
    raw = subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-c:v',
            'libvpx-vp9',
            '-i',
            str(result),
            '-frames:v',
            '1',
            '-f',
            'rawvideo',
            '-pix_fmt',
            'rgba',
            '-',
        ],
        capture_output=True,
        check=True,
    ).stdout
    alpha = raw[3::4]
    assert result.suffix == '.webm'
    assert stream['codec_name'] == 'vp9'
    tags = {key.lower(): value for key, value in stream.get('tags', {}).items()}
    assert tags.get('alpha_mode') == '1'
    assert alpha and 0 < max(alpha) < 255
