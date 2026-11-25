"""Transcripción con hablantes (spec 035, AC-9): palabras y segmentos con su hablante; progreso en dos tramos."""

import json
import shutil
import wave
from pathlib import Path

import pytest

from content_studio import paths
from content_studio.common import progress as progress_protocol
from content_studio.diarization import run, transcribe_speakers_main

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')

WORDS = {
    'language': 'es',
    'language_probability': 0.99,
    'duration': 4.0,
    'text': 'hola amigo mundo',
    'segments': [
        {
            'start': 0.0,
            'end': 1.5,
            'text': 'hola amigo',
            'words': [
                {'start': 0.0, 'end': 0.6, 'word': 'hola', 'probability': 0.9},
                {'start': 0.9, 'end': 1.5, 'word': 'amigo', 'probability': 0.9},
            ],
        },
        {
            'start': 2.5,
            'end': 3.0,
            'text': 'mundo',
            'words': [{'start': 2.5, 'end': 3.0, 'word': 'mundo', 'probability': 0.9}],
        },
    ],
}
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
    'embeddings': {'SPEAKER_00': [0.1], 'SPEAKER_01': [0.2]},
}


def _wav(path: Path, seconds: float) -> Path:
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b'\x00\x00' * int(16000 * seconds))
    return path


@needs_ffmpeg
def test_ac9_words_and_segments_carry_the_speaker(tmp_path, monkeypatch, capsys):
    """AC-9: words.json trae speaker en cada palabra y en cada segmento, y speakers.json junto a él."""
    monkeypatch.setattr(paths, 'data_dir', lambda: tmp_path / 'data')

    def child(command, emit):
        assert 'content_studio.transcription.transcribe_main' in command
        Path(command[command.index('--out') + 1]).write_text(json.dumps(WORDS), encoding='utf-8')
        emit(0.5, 'transcribe')

    def model(wav, counts, emit):
        emit(0.5, 'embeddings')
        return dict(RESULT)

    monkeypatch.setattr(run, 'run_child', child)
    monkeypatch.setattr(run, 'run_model', model)
    audio = _wav(tmp_path / 'audio.wav', 4.0)
    out = tmp_path / 'job' / 'words.json'

    assert (
        transcribe_speakers_main.main(
            ['--input', str(audio), '--model', 'large-v3-turbo', '--language', 'es', '--out', str(out)]
        )
        == 0
    )

    words = json.loads(out.read_text(encoding='utf-8'))
    assert [segment['speaker'] for segment in words['segments']] == ['SPEAKER_00', 'SPEAKER_01']
    assert words['segments'][0]['words'][0]['speaker'] == 'SPEAKER_00'
    assert words['segments'][1]['words'][0]['speaker'] == 'SPEAKER_01'
    assert (out.parent / 'speakers.json').is_file()

    values = []
    for line in capsys.readouterr().out.splitlines():
        parsed = progress_protocol.parse(line)
        if parsed:
            values.append(parsed['p'])
    assert any(value <= 0.6 for value in values)
    assert any(0.6 < value <= 0.95 for value in values)
