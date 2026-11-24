"""Render de subtítulos en el Editor (spec 019, AC-6)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.editor import render_audio, render_video
from content_studio.subtitles.sources import from_cleaner
from content_studio.system import tools


def _project() -> dict:
    return {
        'version': 3,
        'name': 'Prueba',
        'canvas': {'width': 320, 'height': 180, 'fps': 1, 'background': '#203040'},
        'tracks': [
            {
                'id': 'subs',
                'kind': 'subtitles',
                'name': 'Subtítulos',
                'subtitles_project': '7',
                'locked': False,
            }
        ],
        'clips': [],
        'transitions': [],
        'markers': [],
    }


def _subtitle_document() -> dict:
    return from_cleaner(
        [{'word': 'PRUEBA', 'start': 0.0, 'end': 0.9}],
        source_path='mezcla.wav',
        language='es',
    )


def _white_pixels(raw: bytes) -> int:
    return sum(
        1
        for offset in range((50 * 320) * 3, len(raw), 3)
        if raw[offset] > 180 and raw[offset + 1] > 180 and raw[offset + 2] > 180
    )


@pytest.mark.skipif(
    shutil.which('ffmpeg') is None or not tools.detect()['subtitles_filter'], reason='necesita FFmpeg con libass'
)
def test_ac6_editor_frame_burns_the_project_subtitles(tmp_path: Path):
    """AC-6: el filtro pinta texto del proyecto 014 sobre el cuadro exportado."""
    frame = tmp_path / 'frame.png'

    render_video.render_frame(_project(), tmp_path, 0, frame, subtitle_documents={'7': _subtitle_document()})

    raw = subprocess.run(
        [
            shutil.which('ffmpeg'),
            '-v',
            'error',
            '-i',
            str(frame),
            '-f',
            'rawvideo',
            '-pix_fmt',
            'rgb24',
            '-',
        ],
        capture_output=True,
        check=True,
    ).stdout
    assert _white_pixels(raw) > 20


@pytest.mark.skipif(
    shutil.which('ffmpeg') is None or not tools.detect()['subtitles_filter'], reason='necesita FFmpeg con libass'
)
def test_ac6_editor_video_export_burns_the_project_subtitles(tmp_path: Path):
    """AC-6: la exportación de video integra el proyecto ASS al final del grafo visual."""
    video = tmp_path / 'subtitled.mp4'

    render_video.render(
        _project(),
        tmp_path,
        video,
        subtitle_documents={'7': _subtitle_document()},
        burn_subtitles=True,
    )

    raw = subprocess.run(
        [
            shutil.which('ffmpeg'),
            '-v',
            'error',
            '-i',
            str(video),
            '-frames:v',
            '1',
            '-f',
            'rawvideo',
            '-pix_fmt',
            'rgb24',
            '-',
        ],
        capture_output=True,
        check=True,
    ).stdout
    assert video.is_file()
    assert _white_pixels(raw) > 20


def test_ac6_editor_refuses_burn_without_libass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """AC-6: sin libass la exportación con una pista queda bloqueada con el código compartido de subtítulos."""
    monkeypatch.setattr(tools, 'detect', lambda: {'ffmpeg': None, 'git': None, 'gpu': None, 'subtitles_filter': False})

    with pytest.raises(render_audio.RenderError) as error:
        render_video.render_frame(
            _project(), tmp_path, 0, tmp_path / 'frame.png', subtitle_documents={'7': _subtitle_document()}
        )

    assert error.value.code == 'ffmpeg_no_libass'
    assert not (tmp_path / 'frame.png').exists()
