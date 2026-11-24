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


def test_no_lm_flag_reaches_the_engine_command(tmp_path):
    cmd = music.build_command({**VALID, 'no_lm': True}, tmp_path / 'job')

    assert '--no-lm' in cmd


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
        ({**VALID, 'duration': 700}, 'duration_over_max'),
        ({**VALID, 'duration': 0}, 'invalid_duration'),
    ],
)
def test_invalid_params_report_a_code(installed, params, code):
    assert [error['code'] for error in music.validate(params)] == [code]


def test_engine_not_installed_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'MUSIC', tmp_path)  # sin venv

    assert [error['code'] for error in music.validate(VALID)] == ['engine_not_installed']


def test_group_key_is_the_same_for_the_variants_of_one_request_and_ignores_the_seed():
    """AC-8 (D-6): las variantes de un pedido comparten grupo, y la semilla no cuenta para formarlo."""
    one = {**VALID, 'style': ['lofi-chill', 'corporate'], 'variants': 2, 'seed': 1}
    other_seed = {**one, 'seed': 2}

    assert music.group_key(one) == music.group_key(other_seed)
    assert music.group_key(one).startswith('music:')


def test_group_key_changes_with_the_request():
    assert music.group_key({**VALID, 'style': ['lofi-chill']}) != music.group_key({**VALID, 'style': ['corporate']})


def test_prepare_gives_the_params_and_their_group_key():
    params, group = music.prepare(None, VALID)

    assert params == VALID
    assert group == music.group_key(VALID)
