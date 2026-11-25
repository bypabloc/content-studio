"""Trabajos diarize y diarize.split (spec 035, AC-5 y AC-7): ffmpeg en el server; pyannote solo por run."""

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import pytest

from content_studio import paths
from content_studio.common import process
from content_studio.diarization import job_main, run

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def _wav(path: Path, seconds: float) -> Path:
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b'\x00\x00' * int(16000 * seconds))
    return path


@needs_ffmpeg
def test_ac7_diarize_job_leaves_the_turn_files(tmp_path, monkeypatch):
    """AC-7: la carpeta del trabajo termina con turns.json, turns.rttm, turns.csv y speakers.json."""
    monkeypatch.setattr(paths, 'data_dir', lambda: tmp_path / 'data')
    result = {
        'duration': 4.0,
        'speakers': ['SPEAKER_00'],
        'diarization': [{'start': 0.0, 'end': 4.0, 'speaker': 'SPEAKER_00'}],
        'exclusive_diarization': [{'start': 0.0, 'end': 4.0, 'speaker': 'SPEAKER_00'}],
        'embeddings': {'SPEAKER_00': [0.1]},
    }
    monkeypatch.setattr(run, 'run_model', lambda wav, counts, emit: dict(result))
    audio = _wav(tmp_path / 'audio.wav', 4.0)
    out = tmp_path / 'job'

    assert job_main.main(['diarize', '--input', str(audio), '--out', str(out)]) == 0

    for name in ('turns.json', 'turns.rttm', 'turns.csv', 'speakers.json', 'embeddings.json'):
        assert (out / name).is_file()


@needs_ffmpeg
def test_ac5_split_writes_one_wav_per_speaker(tmp_path):
    """AC-5: diarize.split deja speakers/<id>.wav por hablante, con el largo y la frecuencia del original."""
    audio = _wav(tmp_path / 'audio.wav', 4.0)
    turns = tmp_path / 'turns'
    turns.mkdir()
    (turns / 'turns.json').write_text(
        json.dumps(
            {
                'duration': 4.0,
                'speakers': ['SPEAKER_00', 'SPEAKER_01'],
                'diarization': [],
                'exclusive_diarization': [
                    {'start': 0.0, 'end': 1.0, 'speaker': 'SPEAKER_00'},
                    {'start': 2.0, 'end': 3.0, 'speaker': 'SPEAKER_01'},
                ],
            }
        ),
        encoding='utf-8',
    )
    out = tmp_path / 'split'

    assert job_main.main(['split', '--input', str(audio), '--turns', str(turns), '--out', str(out)]) == 0

    for speaker in ('SPEAKER_00', 'SPEAKER_01'):
        with wave.open(str(out / 'speakers' / f'{speaker}.wav'), 'rb') as handle:
            assert handle.getframerate() == 16000
            assert abs(handle.getnframes() / 16000 - 4.0) <= 0.01


def test_the_module_runs_as_a_command():
    """La cola lanza `python -m ...job_main`: el módulo debe ejecutar su acción, no solo cargar."""
    result = subprocess.run(
        [sys.executable, '-m', 'content_studio.diarization.job_main', '--help'],
        capture_output=True,
        text=True,
        check=False,
        env=process.env_src(),
    )

    assert result.returncode == 0
    assert 'diarize' in result.stdout
    assert 'split' in result.stdout
