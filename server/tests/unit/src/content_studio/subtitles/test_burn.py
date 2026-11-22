"""Quemar subtítulos (spec 014, D-7; AC-6 y AC-7): el filtro `subtitles` de ffmpeg con libass y el escape de rutas."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from content_studio.common import ffmpeg as ff
from content_studio.subtitles import burn, burn_main
from content_studio.subtitles.document import save
from content_studio.subtitles.sources import from_cleaner
from content_studio.system import tools

WORDS = [
    {'word': 'hola', 'start': 0.2, 'end': 0.9},
    {'word': 'mundo', 'start': 1.0, 'end': 1.8},
]


def _has_libass() -> bool:
    filters = subprocess.run(['ffmpeg', '-hide_banner', '-filters'], capture_output=True, text=True, check=False)
    return ' subtitles ' in filters.stdout


def _vertical_video(folder: Path) -> Path:
    """Un video vertical de 1080×1920 de 3 s con audio mudo, generado con ffmpeg."""
    video = folder / 'vertical.mp4'
    ff.ffmpeg(
        '-y',
        '-f', 'lavfi', '-i', 'color=c=0x203040:s=1080x1920:d=3:r=25',
        '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono',
        '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
        str(video),
    )  # fmt: skip
    return video


def _highlight_pixels(raw: bytes, width: int, height: int) -> int:
    """Píxeles de la franja central que son del amarillo de resaltado (#FFD400, con tolerancia)."""
    count = 0
    for y in range(height // 2 - 160, height // 2 + 160):
        row = raw[y * width * 3 : (y + 1) * width * 3]
        for x in range(0, len(row), 3):
            red, green, blue = row[x], row[x + 1], row[x + 2]
            if red >= 200 and 150 <= green <= 240 and blue <= 90:
                count += 1
    return count


def test_the_filter_path_escapes_the_drive_colon_and_keeps_the_spaces():
    """AC-7: una ruta de Windows con `:` y espacios queda válida para el filtro `subtitles`."""
    assert burn.filter_path(r'C:\Mis videos\sub titulo.ass') == "'C\\:/Mis videos/sub titulo.ass'"


@pytest.mark.skipif(not _has_libass(), reason='el ffmpeg de este equipo no trae libass')
def test_reels_burned_keeps_the_size_and_the_duration_and_paints_the_highlight(tmp_path):
    """AC-6: reels quemado conserva 1080×1920 y los 3 s, y en el centro hay píxeles del amarillo de resaltado."""
    video = _vertical_video(tmp_path)
    doc_path = tmp_path / 'proyecto' / 'subtitles.json'
    save(from_cleaner(WORDS, source_path=str(video), language='es'), doc_path)
    out = tmp_path / 'salida'

    assert burn_main.main(['--doc', str(doc_path), '--out', str(out), '--preset', 'reels']) == 0

    burned = out / 'subtitled.mp4'
    assert ff.video_size(burned) == (1080, 1920)
    assert abs(ff.probe_duration(burned) - 3.0) < 0.1
    frame = subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', '0.5', '-i', str(burned),
         '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True, check=True,
    ).stdout  # fmt: skip
    assert _highlight_pixels(frame, 1080, 1920) > 50


def test_without_libass_the_job_exits_with_code_3_and_writes_no_video(tmp_path, monkeypatch):
    """Sin libass en el ffmpeg del sistema, el trabajo sale con código 3 (`ffmpeg_no_libass`) y no escribe el video."""
    video = tmp_path / 'clip.mp4'
    doc_path = tmp_path / 'proyecto' / 'subtitles.json'
    save(from_cleaner(WORDS, source_path=str(video), language='es'), doc_path)
    monkeypatch.setattr(tools, 'detect', lambda: {'ffmpeg': None, 'git': None, 'gpu': None, 'subtitles_filter': False})

    assert burn_main.main(['--doc', str(doc_path), '--out', str(tmp_path / 'salida')]) == 3
    assert not (tmp_path / 'salida' / 'subtitled.mp4').exists()
