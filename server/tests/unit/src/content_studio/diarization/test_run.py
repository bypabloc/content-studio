"""Atajos de la diarización (spec 035, D-7): audio de menos de 3 s o un solo hablante no lanzan pyannote (AC-8)."""

import json
import sys
import wave
from pathlib import Path

import pytest

from content_studio import paths
from content_studio.common import process
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


def test_run_child_relays_progress_lines_to_emit():
    """El @@progress del hijo llega a emit con su fracción y su etapa; las demás líneas no cuentan."""
    emitted = []
    command = [
        sys.executable,
        '-c',
        "import json; print('@@progress ' + json.dumps({'p': 0.5, 'stage': 'x'})); print('plain line')",
    ]

    run.run_child(command, lambda fraction, stage: emitted.append((fraction, stage)))

    assert emitted == [(0.5, 'x')]


def test_run_child_fails_with_the_last_lines_of_the_child():
    """Un hijo que sale con error hace fallar el trabajo, con sus últimas líneas como motivo."""
    command = [sys.executable, '-c', "import sys; print('boom: no GPU'); sys.exit(3)"]

    with pytest.raises(RuntimeError, match='boom: no GPU'):
        run.run_child(command, lambda fraction, stage: None)


def test_run_model_passes_the_speaker_flags_and_reads_the_child_result(tmp_path, monkeypatch):
    """run_model corre diarize_main con los hablantes pedidos y devuelve turns.json con sus embeddings."""
    seen = {}

    def child(command, emit):
        seen['command'] = command
        out = Path(command[command.index('--out') + 1])
        out.mkdir(parents=True, exist_ok=True)
        turns = {'duration': 4.0, 'speakers': ['SPEAKER_00'], 'diarization': [], 'exclusive_diarization': []}
        (out / 'turns.json').write_text(json.dumps(turns), encoding='utf-8')
        (out / 'embeddings.json').write_text(json.dumps({'SPEAKER_00': [0.5]}), encoding='utf-8')
        emit(0.5, 'embeddings')

    monkeypatch.setattr(process, 'python_de', lambda venv: Path('python-diarize'))
    monkeypatch.setattr(run, 'run_child', child)
    emitted = []

    result = run.run_model(
        tmp_path / 'audio.wav', {'num_speakers': 2, 'max_speakers': 4}, lambda f, s: emitted.append(f)
    )

    command = seen['command']
    assert command[1:3] == ['-m', 'content_studio.diarization.diarize_main']
    assert command[command.index('--speakers') + 1] == '2'
    assert command[command.index('--max-speakers') + 1] == '4'
    assert result == {
        'duration': 4.0,
        'speakers': ['SPEAKER_00'],
        'diarization': [],
        'exclusive_diarization': [],
        'embeddings': {'SPEAKER_00': [0.5]},
    }
    assert emitted == [0.5]
