"""Render real de cuadros y exportaciones de video con pistas de subtítulos del Editor."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.editor import project as editor_project
from content_studio.editor import render_audio, render_video
from content_studio.subtitles.sources import from_cleaner
from content_studio.system import tools

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'editor'


def _project() -> dict:
    source = json.loads((FIXTURES / 'valid-visual-v2.json').read_text(encoding='utf-8'))['doc']
    doc = editor_project.migrate(source)
    clip = next(item for item in doc['clips'] if item.get('media') == 'video')
    clip.update(src='parity-effects-base.png', src_in=0, src_out=2, start=0, speed=1, media='image')
    doc['clips'] = [clip]
    doc['tracks'] = [track for track in doc['tracks'] if track['id'] == clip['track']]
    doc['tracks'].append(
        {'id': 'subs', 'kind': 'subtitles', 'name': 'Subtítulos', 'subtitles_project': '7', 'locked': False}
    )
    doc['canvas'].update(width=320, height=180, fps=24)
    doc['transitions'] = []
    return doc


def _document() -> dict:
    return from_cleaner([{'word': 'PRUEBA', 'start': 0.0, 'end': 0.9}], source_path='mezcla.wav', language='es')


def _white_pixels(path: Path) -> int:
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True,
        check=True,
    ).stdout
    return sum(1 for offset in range((50 * 320) * 3, len(raw), 3) if min(raw[offset : offset + 3]) > 180)


@pytest.mark.skipif(
    shutil.which('ffmpeg') is None or not tools.detect()['subtitles_filter'], reason='necesita FFmpeg con libass'
)
def test_editor_frame_burns_subtitles_at_the_global_time(tmp_path: Path):
    """El cuadro respeta el tiempo del cabezal al dibujar el cue y omite el cue fuera de rango."""
    project = _project()
    document = _document()
    first, later = tmp_path / 'first.png', tmp_path / 'later.png'

    render_video.render_frame(project, FIXTURES, 0.25, first, subtitle_documents={'7': document})
    render_video.render_frame(project, FIXTURES, 1.25, later, subtitle_documents={'7': document})

    assert _white_pixels(first) > 20
    assert _white_pixels(later) == 0


@pytest.mark.skipif(
    shutil.which('ffmpeg') is None or not tools.detect()['subtitles_filter'], reason='necesita FFmpeg con libass'
)
def test_editor_video_export_burns_project_subtitles(tmp_path: Path):
    """La exportación integra el ASS después de componer las capas visuales."""
    video = tmp_path / 'subtitled.mp4'

    render_video.render(_project(), FIXTURES, video, subtitle_documents={'7': _document()}, burn_subtitles=True)

    assert video.is_file()
    assert _white_pixels(video) > 20


def test_editor_frame_rejects_subtitle_burn_without_libass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Sin libass, una pista activa produce el error compartido sin dejar un cuadro parcial."""
    monkeypatch.setattr(tools, 'detect', lambda: {'ffmpeg': None, 'git': None, 'gpu': None, 'subtitles_filter': False})

    with pytest.raises(render_audio.RenderError, match='ffmpeg_no_libass'):
        render_video.render_frame(
            _project(), FIXTURES, 0, tmp_path / 'frame.png', subtitle_documents={'7': _document()}
        )

    assert not (tmp_path / 'frame.png').exists()
