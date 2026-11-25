"""Atajos de la diarización (spec 035, D-7): audio de menos de 3 s o un solo hablante no lanzan pyannote (AC-8)."""

import wave
from pathlib import Path

import pytest

from content_studio import paths
from content_studio.diarization import run


def _wav(path: Path, seconds: float) -> Path:
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b'\x00\x00' * int(16000 * seconds))
    return path


@pytest.fixture
def no_model(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, 'data_dir', lambda: tmp_path / 'data')

    def refuse(wav, counts, emit):
        raise AssertionError('the model must not run')

    monkeypatch.setattr(run, 'run_model', refuse)


def test_ac8_short_audio_is_one_speaker_without_the_model(tmp_path, no_model):
    """AC-8: menos de 3 s es un solo hablante que cubre todo el audio, y su turns.json se escribe."""
    wav = _wav(tmp_path / 'short.wav', 2.0)

    result = run.diarize_file(wav, wav, tmp_path / 'out', {}, emit=lambda p, s: None)

    assert result['speakers'] == ['SPEAKER_00']
    assert result['exclusive_diarization'] == [{'start': 0.0, 'end': 2.0, 'speaker': 'SPEAKER_00'}]
    assert (tmp_path / 'out' / 'turns.json').is_file()


def test_ac8_one_speaker_request_skips_the_model(tmp_path, no_model):
    """AC-8: pedir num_speakers=1 da un solo hablante sin lanzar el modelo."""
    wav = _wav(tmp_path / 'long.wav', 4.0)

    result = run.diarize_file(wav, wav, tmp_path / 'out', {'num_speakers': 1}, emit=lambda p, s: None)

    assert result['speakers'] == ['SPEAKER_00']
