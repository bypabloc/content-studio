"""Trabajo `voice.build` (spec 010, D-5 y AC-7): valida las voces, arma el comando y reporta el progreso."""

from __future__ import annotations

import json
import sys

import pytest

from content_studio.common import progress
from content_studio.narration.voices import main as voices_main
from content_studio.services import voice_build
from content_studio.services.registry import SERVICES


def test_ac7_the_build_is_a_service_that_takes_the_gpu():
    assert SERVICES['voice.build'] is voice_build
    assert voice_build.RESOURCE == 'gpu'


def test_ac7_only_voices_of_the_catalog_are_valid():
    assert voice_build.validate({'voices': ['yesid', 'andrea']}) == []
    assert voice_build.validate({'voices': ['no-existe']}) == [
        {'code': 'unknown_voice', 'params': {'voice': 'no-existe'}}
    ]


def test_ac7_a_build_without_voices_is_rejected():
    assert voice_build.validate({'voices': []}) == [{'code': 'no_voices', 'params': {}}]


def test_ac7_the_command_runs_the_catalog_main_for_each_voice(tmp_path):
    command = voice_build.build_command({'voices': ['yesid', 'andrea'], 'force': True}, tmp_path)

    assert command[0] == sys.executable
    assert command[1:] == ['-m', 'content_studio.narration.voices.main', '--build', 'yesid', 'andrea', '--force']


def test_ac7_without_force_the_command_has_no_force_flag(tmp_path):
    command = voice_build.build_command({'voices': ['yesid']}, tmp_path)

    assert '--force' not in command


def test_ac7_a_simulated_build_reports_progress_by_voice_and_style_and_ends_at_one(monkeypatch, capsys):
    """El build de cada voz emite un paso por estilo; el progreso del trabajo sube sin retroceder y llega a 1."""

    def simulated_build(name, sheet, force, span):
        for done in (1, 2):
            progress.emit(progress.span_fraction(span, done, 2), f'{name} · paso {done}')
        return True

    monkeypatch.setattr(voices_main, 'build', simulated_build)
    monkeypatch.setattr(voices_main.process, 'use_venv', lambda *args, **kwargs: None)
    monkeypatch.setattr(sys, 'argv', ['voices', '--build', 'yesid', 'andrea'])

    with pytest.raises(SystemExit) as stop:
        voices_main.main()

    out = capsys.readouterr().out
    fractions = [
        json.loads(line.removeprefix(progress.PREFIX))['p']
        for line in out.splitlines()
        if line.startswith(progress.PREFIX)
    ]
    assert stop.value.code == 0
    assert len(fractions) == 4
    assert fractions == sorted(fractions) and fractions[-1] == 1.0
