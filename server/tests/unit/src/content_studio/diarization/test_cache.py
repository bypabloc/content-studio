"""Caché de diarizaciones: el mismo audio y el mismo número de hablantes reusan su resultado (spec 035, AC-8)."""

import wave
from pathlib import Path

from content_studio import paths
from content_studio.diarization import cache, run

RESULT = {
    'duration': 4.0,
    'speakers': ['SPEAKER_00', 'SPEAKER_01'],
    'diarization': [
        {'start': 0.0, 'end': 2.0, 'speaker': 'SPEAKER_00'},
        {'start': 2.0, 'end': 4.0, 'speaker': 'SPEAKER_01'},
    ],
    'exclusive_diarization': [
        {'start': 0.0, 'end': 2.0, 'speaker': 'SPEAKER_00'},
        {'start': 2.0, 'end': 4.0, 'speaker': 'SPEAKER_01'},
    ],
    'embeddings': {'SPEAKER_00': [0.1, 0.2], 'SPEAKER_01': [0.3, 0.4]},
}


def _wav(path: Path, seconds: float) -> Path:
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b'\x00\x00' * int(16000 * seconds))
    return path


def test_ac8_same_audio_and_speakers_reuse_the_result(tmp_path, monkeypatch):
    """AC-8: la segunda vez no lanza el modelo, reusa <datos>/diarizations/<sha1>.json y escribe sus archivos."""
    monkeypatch.setattr(paths, 'data_dir', lambda: tmp_path / 'data')
    calls = []

    def model(wav, counts, emit):
        calls.append(counts)
        return dict(RESULT)

    monkeypatch.setattr(run, 'run_model', model)
    wav = _wav(tmp_path / 'audio.wav', 4.0)

    first = run.diarize_file(wav, wav, tmp_path / 'first', {}, emit=lambda p, s: None)
    second = run.diarize_file(wav, wav, tmp_path / 'second', {}, emit=lambda p, s: None)

    assert calls == [{}]
    assert second == first
    assert cache.json_path(cache.cache_key(wav, {})).is_file()
    assert (tmp_path / 'second' / 'turns.json').is_file()


def test_ac8_another_speaker_count_is_another_entry(tmp_path, monkeypatch):
    """AC-8: con otro número de hablantes la caché no sirve: el modelo corre otra vez."""
    monkeypatch.setattr(paths, 'data_dir', lambda: tmp_path / 'data')
    calls = []

    def model(wav, counts, emit):
        calls.append(counts)
        return dict(RESULT)

    monkeypatch.setattr(run, 'run_model', model)
    wav = _wav(tmp_path / 'audio.wav', 4.0)

    run.diarize_file(wav, wav, tmp_path / 'first', {}, emit=lambda p, s: None)
    run.diarize_file(wav, wav, tmp_path / 'second', {'num_speakers': 2}, emit=lambda p, s: None)

    assert calls == [{}, {'num_speakers': 2}]
