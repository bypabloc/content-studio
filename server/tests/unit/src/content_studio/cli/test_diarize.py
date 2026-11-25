"""Subcomando studio diarize (spec 035, AC-11): encola, muestra la carpeta y rechaza hablantes mal pedidos."""

import json

import pytest

from content_studio.cli import main, submit


@pytest.fixture
def audio(tmp_path):
    path = tmp_path / 'audio.wav'
    path.write_bytes(b'RIFF')
    return path


def test_ac11_zero_speakers_exits_two_with_an_english_message(audio, capsys):
    """AC-11: --speakers 0 sale con 2 y un mensaje en inglés, sin encolar nada."""
    code = main.main(['diarize', str(audio), '--speakers', '0'])

    assert code == 2
    assert 'between 1 and 20' in capsys.readouterr().err


def test_ac11_min_over_max_exits_two(audio, capsys):
    """AC-11: --min-speakers 3 --max-speakers 2 sale con 2 y dice por qué."""
    code = main.main(['diarize', str(audio), '--min-speakers', '3', '--max-speakers', '2'])

    assert code == 2
    assert 'cannot be greater than --max-speakers' in capsys.readouterr().err


def test_ac11_queues_the_job_and_prints_its_folder(audio, monkeypatch, capsys, tmp_path):
    """AC-11: encola el trabajo con el audio y el número de hablantes, y muestra la carpeta de salida."""
    seen = {}

    def execute(kind, params, db, main_path):
        seen.update(kind=kind, params=params)
        return {'job': 7, 'status': 'done', 'output_dir': str(tmp_path / 'out')}

    monkeypatch.setattr(submit, 'execute', execute)

    code = main.main(['diarize', str(audio), '--speakers', '2'])

    assert code == 0
    assert seen == {'kind': 'diarize', 'params': {'input': str(audio), 'num_speakers': 2}}
    assert json.loads(capsys.readouterr().out)['output_dir'] == str(tmp_path / 'out')


def test_ac11_help_asks_nothing(capsys):
    """AC-11: --help muestra la ayuda y sale con 0, sin preguntar nada."""
    with pytest.raises(SystemExit) as stop:
        main.main(['diarize', '--help'])

    assert stop.value.code == 0
