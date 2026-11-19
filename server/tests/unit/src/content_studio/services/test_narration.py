"""Servicio de narración (spec 004, D-2): valida los parámetros de la cola y arma el comando del motor."""

from __future__ import annotations

import sys

import pytest

from content_studio import paths
from content_studio.services import narration

VALID = {'model': 'qwen-0.6b', 'style': 'expert', 'text': 'Hola.'}


@pytest.fixture
def installed(tmp_path, monkeypatch):
    """Finge que el venv del motor existe: `installed()` mira la carpeta de datos."""
    monkeypatch.setattr(paths, 'NARRATION', tmp_path)
    (tmp_path / narration.ENGINES['qwen-0.6b'].venv).mkdir()


def test_build_command_runs_the_tts_module_with_the_job_folder_as_output(tmp_path):
    cmd = narration.build_command(VALID, tmp_path / 'job')

    assert cmd[0] == sys.executable
    assert cmd[cmd.index('-m') + 1] == 'content_studio.narration.tts'
    assert cmd[cmd.index('--model') + 1] == 'qwen-0.6b'
    assert cmd[cmd.index('--style') + 1] == 'expert'
    assert cmd[cmd.index('--text') + 1] == 'Hola.'
    assert cmd[cmd.index('--output') + 1] == str(tmp_path / 'job')


def test_valid_params_have_no_errors(installed):
    assert narration.validate(VALID) == []


@pytest.mark.parametrize(
    ('params', 'code'),
    [
        ({**VALID, 'model': 'nope'}, 'unknown_engine'),
        ({**VALID, 'style': 'nope'}, 'unknown_style'),
        ({'model': 'qwen-0.6b', 'style': 'expert'}, 'missing_text'),
    ],
)
def test_invalid_params_report_a_code(installed, params, code):
    assert [error['code'] for error in narration.validate(params)] == [code]


def test_engine_not_installed_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'NARRATION', tmp_path)  # sin venv

    assert [error['code'] for error in narration.validate(VALID)] == ['engine_not_installed']
