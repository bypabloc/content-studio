"""Servicio de música (spec 004, D-2): valida los parámetros de la cola y arma el comando del motor."""

from __future__ import annotations

import sys

import pytest

from content_studio import paths
from content_studio.services import music

VALID = {'model': 'acestep', 'style': ['lofi-chill'], 'duration': 15}


@pytest.fixture
def installed(tmp_path, monkeypatch):
    """Finge que el venv del motor existe: `installed()` mira la carpeta de datos."""
    monkeypatch.setattr(paths, 'MUSIC', tmp_path)
    (tmp_path / music.MODELS['acestep'].venv).mkdir()


def test_build_command_runs_the_music_module_into_the_job_folder(tmp_path):
    cmd = music.build_command(VALID, tmp_path / 'job')

    assert cmd[0] == sys.executable
    assert cmd[cmd.index('-m') + 1] == 'content_studio.music.music_main'
    assert cmd[cmd.index('--model') + 1] == 'acestep'
    assert cmd[cmd.index('--style') + 1] == 'lofi-chill'
    assert cmd[cmd.index('--duration') + 1] == '15'
    assert cmd[cmd.index('--folder') + 1] == str(tmp_path / 'job')


def test_valid_params_have_no_errors(installed):
    assert music.validate(VALID) == []


def test_free_text_style_needs_key_and_bpm(installed):
    free = {**VALID, 'style': ['synthwave, retro 80s']}

    assert [error['code'] for error in music.validate(free)] == ['style_needs_key_bpm']
    assert music.validate({**free, 'key': 'E Minor', 'bpm': 105}) == []


@pytest.mark.parametrize(
    ('params', 'code'),
    [
        ({**VALID, 'model': 'nope'}, 'unknown_engine'),
        ({**VALID, 'duration': 700}, 'invalid_duration'),
        ({**VALID, 'duration': 0}, 'invalid_duration'),
    ],
)
def test_invalid_params_report_a_code(installed, params, code):
    assert [error['code'] for error in music.validate(params)] == [code]


def test_engine_not_installed_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'MUSIC', tmp_path)  # sin venv

    assert [error['code'] for error in music.validate(VALID)] == ['engine_not_installed']
