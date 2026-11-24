"""Servicio `media.split` de la cola (spec 015, D-5): valida el corte y arma el comando de `edit split`."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_studio.services import media_split


def test_the_service_runs_on_cpu_without_the_gpu_lock():
    """Dividir es ffmpeg: la cola no toma el candado de la GPU."""
    assert media_split.RESOURCE == 'cpu'


def test_validate_accepts_a_step_or_increasing_markers():
    """Cada N segundos (> 0) o marcas crecientes y positivas no dan errores."""
    assert media_split.validate({'input': 'a.wav', 'every': 600}) == []
    assert media_split.validate({'input': 'a.wav', 'markers': [60, 120]}) == []


@pytest.mark.parametrize('params', [{'every': 0}, {'markers': [120, 60]}, {'markers': [0, 60]}])
def test_validate_names_an_invalid_split(params):
    """Un paso nulo, marcas que no crecen o una marca en 0 dan `invalid_split`."""
    assert media_split.validate({'input': 'a.wav', **params}) == [{'code': 'invalid_split', 'params': {}}]


def test_build_command_splits_by_markers_into_the_job_folder(tmp_path: Path):
    """El comando corre `edit split` con las marcas y el nombre de la fuente como raíz de las partes."""
    command = media_split.build_command({'input': 'long-talk.wav', 'markers': [60, 120]}, tmp_path)

    assert command[1:4] == ['-m', 'content_studio.media.edit', 'split']
    assert command[command.index('--stem') + 1] == 'long-talk'
    assert command[command.index('--out-dir') + 1] == str(tmp_path)
    assert command[command.index('--markers') + 1 : command.index('--markers') + 3] == ['60', '120']
    assert '--copy' not in command
