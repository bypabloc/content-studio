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
