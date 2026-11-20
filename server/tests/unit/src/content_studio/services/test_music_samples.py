"""Servicio `music.samples` de la cola (spec 011, D-3): valida los estilos y arma el comando del motor."""

from __future__ import annotations

from pathlib import Path

from content_studio.services import music_samples


def test_an_unknown_style_is_refused_and_the_known_ones_pass():
    assert music_samples.validate({'styles': ['lofi-jazz']}) == []
    assert music_samples.validate({'styles': ['no-existe']}) == [
        {'code': 'unknown_style', 'params': {'style': 'no-existe'}}
    ]


def test_the_command_runs_the_samples_module_with_the_styles_and_force(tmp_path: Path):
    command = music_samples.build_command({'styles': ['lofi-jazz', 'ambient'], 'force': True}, tmp_path)

    assert command[1:3] == ['-m', 'content_studio.music.samples_main']
    assert command[-5:] == ['--styles', 'lofi-jazz', 'ambient', '--force'] or '--force' in command
    assert 'lofi-jazz' in command and 'ambient' in command
