"""Servicio `media.reframe_track` de la cola (spec 015, D-3): corre seguimiento de la persona en su venv, sin la GPU."""

from __future__ import annotations

from pathlib import Path

from content_studio.services import media_reframe_track


def test_the_service_runs_on_cpu_without_the_gpu_lock():
    """YuNet corre en CPU: la cola no toma el candado de la GPU."""
    assert media_reframe_track.RESOURCE == 'cpu'


def test_build_command_passes_the_input_and_the_track_file_in_the_job_folder(tmp_path: Path):
    """El comando corre `face_track_main` y el `track.json` sale en la carpeta del trabajo."""
    command = media_reframe_track.build_command({'input': 'a.mp4'}, tmp_path)

    assert command[1:3] == ['-m', 'content_studio.vision.face_track_main']
    options = dict(zip(command[3::2], command[4::2], strict=False))
    assert options == {'--input': 'a.mp4', '--out': str(tmp_path / 'track.json')}
