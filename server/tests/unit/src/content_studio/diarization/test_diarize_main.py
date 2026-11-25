"""diarize_main: pyannote corre en su venv con la entrada, el lote y el progreso del plan (spec 035, AC-4)."""

import json
import os
import sys
import types
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from content_studio.common import process
from content_studio.common import progress as progress_protocol
from content_studio.diarization import diarize_main


def _write_wav(path: Path, seconds: float = 2.0) -> Path:
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b'\x00\x00' * int(16000 * seconds))
    return path


class _Segment:
    def __init__(self, start: float, end: float) -> None:
        self.start = start
        self.end = end


class FakeAnnotation:
    """Imita pyannote.core.Annotation: turnos (inicio, fin, hablante) y sus etiquetas en orden de aparición."""

    def __init__(self, turns: list[tuple[float, float, str]]) -> None:
        self._turns = turns

    def itertracks(self, yield_label: bool = False):
        for start, end, label in self._turns:
            yield _Segment(start, end), None, label

    def labels(self) -> list[str]:
        return list(dict.fromkeys(label for _, _, label in self._turns))


@pytest.fixture
def pyannote(monkeypatch):
    """pyannote.audio y torch falsos en sys.modules; el dict guarda lo que la llamada recibió."""
    seen: dict = {}

    class FakePipeline:
        @classmethod
        def from_pretrained(cls, path: str) -> 'FakePipeline':
            seen['path'] = path
            return cls()

        def __call__(self, audio: dict, hook, **counts) -> SimpleNamespace:
            seen['audio'] = audio
            seen['counts'] = counts
            seen['batch'] = self.embedding_batch_size
            seen['env'] = {key: os.environ.get(key) for key in ('PYANNOTE_METRICS_ENABLED', 'HF_HUB_OFFLINE')}
            hook('speaker_counting', None)
            hook('segmentation', None, file=None, total=4, completed=2)
            hook('embeddings', None, file=None, total=4, completed=4)
            turns = [(0.0, 1.2, 'SPEAKER_00'), (1.2, 2.0, 'SPEAKER_01')]
            return SimpleNamespace(
                speaker_diarization=FakeAnnotation(turns),
                exclusive_speaker_diarization=FakeAnnotation(turns),
                speaker_embeddings=np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32),
            )

    audio_module = types.ModuleType('pyannote.audio')
    audio_module.Pipeline = FakePipeline
    package = types.ModuleType('pyannote')
    package.audio = audio_module
    torch = types.ModuleType('torch')
    torch.from_numpy = lambda array: array
    torch.device = lambda name: name
    torch.cuda = SimpleNamespace(is_available=lambda: False)
    monkeypatch.setitem(sys.modules, 'pyannote', package)
    monkeypatch.setitem(sys.modules, 'pyannote.audio', audio_module)
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setattr(process, 'use_venv', lambda *args, **kwargs: None)
    monkeypatch.setenv('PYANNOTE_METRICS_ENABLED', '')
    monkeypatch.setenv('HF_HUB_OFFLINE', '')
    return seen


def _run(tmp_path: Path, *extra: str) -> Path:
    audio = _write_wav(tmp_path / 'audio-16k.wav')
    out = tmp_path / 'diarize'
    assert diarize_main.main(['--input', str(audio), '--out', str(out), *extra]) == 0
    return out


def test_ac4_environment_input_and_output(tmp_path, capsys, pyannote):
    """AC-4: entorno offline sin telemetría, carpeta local, lote 4, entrada 16 kHz, progreso creciente y archivos."""
    out = _run(tmp_path)

    assert pyannote['env'] == {'PYANNOTE_METRICS_ENABLED': '0', 'HF_HUB_OFFLINE': '1'}
    assert Path(pyannote['path']).parts[-2:] == ('models', 'community-1')
    assert pyannote['batch'] == 4
    assert pyannote['audio']['sample_rate'] == 16000
    assert pyannote['audio']['waveform'].shape == (1, 32000)
    assert pyannote['audio']['waveform'].dtype == np.float32
    assert pyannote['counts'] == {}

    values = []
    for line in capsys.readouterr().out.splitlines():
        parsed = progress_protocol.parse(line)
        if parsed:
            values.append(parsed['p'])
    assert len(values) >= 2
    assert values == sorted(values)
    assert values[-1] <= 1

    turns = json.loads((out / 'turns.json').read_text(encoding='utf-8'))
    assert turns['duration'] == 2.0
    assert turns['speakers'] == ['SPEAKER_00', 'SPEAKER_01']
    assert turns['exclusive_diarization'][0] == {'start': 0.0, 'end': 1.2, 'speaker': 'SPEAKER_00'}
    assert json.loads((out / 'embeddings.json').read_text(encoding='utf-8')) == {
        'SPEAKER_00': [pytest.approx(0.1), pytest.approx(0.2)],
        'SPEAKER_01': [pytest.approx(0.3), pytest.approx(0.4)],
    }
    speakers = json.loads((out / 'speakers.json').read_text(encoding='utf-8'))
    assert speakers['SPEAKER_01'] == {'name': 'Hablante 2', 'color': '#dc2626'}
    assert (out / 'turns.rttm').is_file()
    assert (out / 'turns.csv').is_file()


def test_ac4_exact_number_of_speakers(tmp_path, pyannote):
    """AC-4: con --speakers, pyannote recibe num_speakers."""
    _run(tmp_path, '--speakers', '2')

    assert pyannote['counts'] == {'num_speakers': 2}


def test_ac4_speaker_range(tmp_path, pyannote):
    """AC-4: con un rango, pyannote recibe min_speakers y max_speakers."""
    _run(tmp_path, '--min-speakers', '2', '--max-speakers', '4')

    assert pyannote['counts'] == {'min_speakers': 2, 'max_speakers': 4}
