"""Audio de un hablante: el comando de ffmpeg que silencia lo que no es suyo (spec 035, AC-5)."""

import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
import pytest

from content_studio.diarization import speaker_audio

TURNS = [
    {'start': 0.0, 'end': 1.2, 'speaker': 'SPEAKER_00'},
    {'start': 2.0, 'end': 3.5, 'speaker': 'SPEAKER_01'},
    {'start': 4.0, 'end': 5.0, 'speaker': 'SPEAKER_01'},
    {'start': 5.5, 'end': 6.0, 'speaker': 'SPEAKER_01'},
]
EXPRESSION = "volume=enable='not(between(t,2.000,3.500)+between(t,4.000,5.000)+between(t,5.500,6.000))':volume=0"


def test_ac5_ffmpeg_command_silences_outside_the_turns(tmp_path):
    """AC-5: el filtro deja pasar solo los turnos del hablante y el códec de salida es PCM."""
    source = tmp_path / 'audio.wav'
    out = tmp_path / 'speakers' / 'SPEAKER_01.wav'

    command = speaker_audio.split_command(source, TURNS, 'SPEAKER_01', out)

    assert command == ['ffmpeg', '-y', '-i', str(source), '-af', EXPRESSION, '-c:a', 'pcm_s16le', str(out)]


def test_ac5_speaker_without_turns_is_silent_everywhere(tmp_path):
    """AC-5: un hablante sin turnos produce un filtro que silencia todo el audio."""
    command = speaker_audio.split_command(tmp_path / 'audio.wav', TURNS, 'SPEAKER_09', tmp_path / 'x.wav')

    assert command[command.index('-af') + 1] == "volume=enable='not(0)':volume=0"


def test_ac5_long_filter_goes_to_a_script_file(tmp_path):
    """AC-5: con muchos turnos el filtro va en un archivo (-filter_script:a), no en la línea de comandos."""
    turns = [{'start': i * 1.0, 'end': i * 1.0 + 0.5, 'speaker': 'SPEAKER_01'} for i in range(2000)]
    out = tmp_path / 'SPEAKER_01.wav'

    command = speaker_audio.split_command(tmp_path / 'audio.wav', turns, 'SPEAKER_01', out)

    script = tmp_path / 'SPEAKER_01.filter.txt'
    assert '-af' not in command
    assert command[command.index('-filter_script:a') + 1] == str(script)
    assert script.read_text(encoding='utf-8').startswith("volume=enable='not(between(t,0.000,0.500)+")


def _tone(path: Path, seconds: float = 5.0, rate: int = 16000) -> Path:
    """Un tono de 440 Hz de `seconds` en WAV mono de 16 bits."""
    t = np.arange(int(seconds * rate)) / rate
    samples = (np.sin(2 * np.pi * 440 * t) * 0.5 * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(samples.tobytes())
    return path


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
@pytest.mark.parametrize('extra_turns', [0, 2000])
def test_ac5_real_ffmpeg_keeps_length_rate_and_silences_the_rest(tmp_path, extra_turns):
    """AC-5 con ffmpeg real: mismo largo y frecuencia que el original, tono dentro del turno y cero fuera."""
    source = _tone(tmp_path / 'tone.wav')
    turns = [{'start': 1.0, 'end': 2.0, 'speaker': 'SPEAKER_01'}]
    turns += [{'start': 10.0 + i, 'end': 10.5 + i, 'speaker': 'SPEAKER_01'} for i in range(extra_turns)]
    out = tmp_path / 'SPEAKER_01.wav'

    subprocess.run(speaker_audio.split_command(source, turns, 'SPEAKER_01', out), check=True, capture_output=True)

    with wave.open(str(out), 'rb') as handle:
        rate = handle.getframerate()
        frames = handle.getnframes()
        data = np.frombuffer(handle.readframes(frames), dtype=np.int16)
    assert rate == 16000
    assert abs(frames / rate - 5.0) <= 0.01
    assert np.abs(data[int(1.2 * rate) : int(1.8 * rate)]).max() > 1000
    assert np.abs(data[int(3.0 * rate) : int(4.0 * rate)]).max() <= 1
