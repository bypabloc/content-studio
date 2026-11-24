"""Servicio `media.trim` de la cola (spec 015, D-5): valida el tramo y arma el comando de `edit trim`."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_studio.media import edit
from content_studio.services import media_trim


def test_the_service_runs_on_cpu_without_the_gpu_lock():
    """Recortar es ffmpeg: la cola no toma el candado de la GPU."""
    assert media_trim.RESOURCE == 'cpu'


def test_validate_accepts_a_span_inside_the_file_with_its_fades():
    """Un tramo con inicio menor que su fin y fundidos que caben en él no da errores."""
    assert media_trim.validate({'input': 'a.wav', 'start': 2, 'end': 4, 'fade_in': 0.5, 'fade_out': 0.5}) == []


@pytest.mark.parametrize(
    'params',
    [
        {'start': 4, 'end': 2},
        {'start': -1, 'end': 2},
        {'start': 2, 'end': 3, 'fade_in': 0.8, 'fade_out': 0.8},
    ],
)
def test_validate_names_an_invalid_cut(params):
    """Un tramo al revés, con inicio negativo o con fundidos más largos que el tramo da `invalid_cut`."""
    assert media_trim.validate({'input': 'a.wav', **params}) == [{'code': 'invalid_cut', 'params': {}}]


def test_build_command_names_the_wav_output_for_audio(monkeypatch, tmp_path: Path):
    """Un audio se recorta a WAV; el comando corre `edit trim` con el tramo y los fundidos."""
    monkeypatch.setattr(edit, 'has_video', lambda path: False)

    command = media_trim.build_command({'input': 'a.mp3', 'start': 2, 'end': 4, 'mode': 'remove'}, tmp_path)

    assert command[1:4] == ['-m', 'content_studio.media.edit', 'trim']
    options = dict(zip(command[4::2], command[5::2], strict=False))
    assert options['--out'] == str(tmp_path / 'cut.wav')
    assert options['--mode'] == 'remove'
    assert options['--fade-in'] == '0.0'
