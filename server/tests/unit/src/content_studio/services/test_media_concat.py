"""Servicio `media.concat` de la cola (spec 015, D-5): valida que los archivos sean del mismo tipo y arma `concat`."""

from __future__ import annotations

from pathlib import Path

from content_studio.media import edit
from content_studio.services import media_concat


def test_the_service_runs_on_cpu_without_the_gpu_lock():
    """Unir es ffmpeg: la cola no toma el candado de la GPU."""
    assert media_concat.RESOURCE == 'cpu'


def test_validate_needs_at_least_two_files(monkeypatch):
    """Unir un solo archivo no tiene sentido: `missing_input`."""
    monkeypatch.setattr(edit, 'has_video', lambda path: False)

    assert media_concat.validate({'inputs': ['a.wav']}) == [{'code': 'missing_input', 'params': {}}]


def test_validate_refuses_audio_and_video_together(monkeypatch):
    """AC-8: un audio y un video en la misma unión dan `mixed_kinds`."""
    monkeypatch.setattr(edit, 'has_video', lambda path: path.endswith('.mp4'))

    assert media_concat.validate({'inputs': ['a.wav', 'b.mp4']}) == [{'code': 'mixed_kinds', 'params': {}}]


def test_build_command_joins_video_into_mp4_with_the_crossfade(monkeypatch, tmp_path: Path):
    """Videos se unen en MP4 con el crossfade pedido."""
    monkeypatch.setattr(edit, 'has_video', lambda path: True)

    command = media_concat.build_command({'inputs': ['a.mp4', 'b.mp4'], 'crossfade': 1.0}, tmp_path)

    assert command[1:4] == ['-m', 'content_studio.media.edit', 'concat']
    assert command[command.index('--out') + 1] == str(tmp_path / 'joined.mp4')
    assert command[command.index('--crossfade') + 1] == '1.0'
