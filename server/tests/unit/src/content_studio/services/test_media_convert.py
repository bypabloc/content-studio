"""Servicio `media.convert` de la cola (spec 015, D-1 a D-3): valida formato, códec y encuadre, y arma el comando."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.services import media_convert

ENCODERS = frozenset({'libx264', 'libmp3lame', 'pcm_s16le', 'aac', 'gif'})


@pytest.fixture(autouse=True)
def encoders(monkeypatch):
    """El ffmpeg de la prueba trae estos códecs: no hace falta ejecutar ffmpeg para validar."""
    monkeypatch.setattr(media_convert, 'available_encoders', lambda: ENCODERS)


def test_the_service_runs_on_cpu_without_the_gpu_lock():
    """Convertir es ffmpeg: la cola no toma el candado de la GPU."""
    assert media_convert.RESOURCE == 'cpu'


def test_validate_accepts_a_known_target_and_reframe_mode():
    """Un formato del catálogo, con su códec en el ffmpeg, y un encuadre conocido no dan errores."""
    params = {'input': 'a.mp4', 'target': 'mp4-h264', 'options': {'reframe': {'mode': 'center'}}}

    assert media_convert.validate(params) == []


def test_validate_names_an_unknown_target():
    """Un formato que no existe da `unknown_target`."""
    assert media_convert.validate({'input': 'a.wav', 'target': 'nope', 'options': {}}) == [
        {'code': 'unknown_target', 'params': {'target': 'nope'}}
    ]


def test_validate_names_a_codec_the_system_ffmpeg_lacks(monkeypatch):
    """Un formato cuyo códec falta en el ffmpeg del equipo da `codec_unavailable` al encolar."""
    monkeypatch.setattr(media_convert, 'available_encoders', lambda: frozenset({'aac'}))

    assert media_convert.validate({'input': 'a.wav', 'target': 'mp3', 'options': {}}) == [
        {'code': 'codec_unavailable', 'params': {'codec': 'libmp3lame'}}
    ]


def test_validate_names_an_unknown_reframe_mode():
    """Un modo de encuadre que no existe da `unknown_reframe`."""
    errors = media_convert.validate(
        {'input': 'a.mp4', 'target': 'mp4-h264', 'options': {'reframe': {'mode': 'spiral'}}}
    )

    assert errors == [{'code': 'unknown_reframe', 'params': {'mode': 'spiral'}}]


def test_build_command_passes_the_target_and_the_options_as_json(tmp_path: Path):
    """El comando corre el conversor con el formato y las opciones en JSON; el resultado va a la carpeta del trabajo."""
    options = {'width': 1080, 'height': 1920, 'reframe': {'mode': 'center'}}

    command = media_convert.build_command({'input': 'a.mp4', 'target': 'mp4-h264', 'options': options}, tmp_path)

    assert command[1:4] == ['-m', 'content_studio.media.convert', '--input']
    assert command[command.index('--target') + 1] == 'mp4-h264'
    assert command[command.index('--out-dir') + 1] == str(tmp_path)
    assert json.loads(command[command.index('--options') + 1]) == options
