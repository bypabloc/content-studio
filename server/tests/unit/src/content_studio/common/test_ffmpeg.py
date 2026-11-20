"""Comandos de ffmpeg y ffprobe que arma common/ffmpeg.py, y los picos de una señal (spec 006, AC-4)."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
from array import array

import pytest

from content_studio import paths
from content_studio.common import ffmpeg


def test_ac4_probe_command_asks_ffprobe_for_the_duration_only():
    assert ffmpeg.probe_command('a.wav') == [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', 'a.wav',
    ]  # fmt: skip


def test_ac4_peaks_command_decodes_mono_8_kHz_s16le_to_a_pipe():
    assert ffmpeg.peaks_command('a.wav') == [
        'ffmpeg', '-v', 'error', '-i', 'a.wav', '-f', 's16le', '-ac', '1', '-ar', '8000', '-',
    ]  # fmt: skip


def test_ac4_window_peaks_always_returns_n_values():
    assert ffmpeg.window_peaks(array('h', [0, 16384, 0, 0]), 2) == [0.5, 0.0]
    assert ffmpeg.window_peaks(array('h', [1000]), 3) == [1000 / 32768, 0.0, 0.0]


def test_window_peaks_has_no_empty_tail_when_the_length_is_not_a_multiple_of_n():
    """La onda no termina en cero: con 16001 muestras y 2000 ventanas, ninguna ventana queda vacía."""
    assert all(p > 0 for p in ffmpeg.window_peaks(array('h', [1000] * 16001), 2000))


def test_loudness_of_silence_reads_the_peak_floor_instead_of_failing():
    verify = '    I:         -70.0 LUFS\n  True peak:\n    Peak:       -inf dBFS\n'

    assert ffmpeg.parse_loudness(verify) == (-70.0, -120.0)


def test_loudness_without_a_summary_is_a_value_error():
    with pytest.raises(ValueError):
        ffmpeg.parse_loudness('')


RATE = 48000
FINGERPRINT = paths.ROOT / 'server' / 'tests' / 'fixtures' / 'voices' / 'client-sine-1s-48k-24b.sha256'


def _client_encoder_bytes() -> bytes:
    """Los bytes que escribe `encodeWav` (client) para una senoidal de 1 s: float32 y redondeo de Math.round."""
    samples = array('f', (math.sin((2 * math.pi * 1000 * i) / RATE) for i in range(RATE)))
    body = bytearray()
    for sample in samples:
        x = max(-1.0, min(1.0, sample))
        value = math.floor(x * (0x800000 if x < 0 else 0x7FFFFF) + 0.5)
        body += (value & 0xFFFFFF).to_bytes(3, 'little')
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(body), b'WAVE', b'fmt ', 16, 1, 1, RATE, RATE * 3, 3, 24, b'data', len(body),
    )  # fmt: skip
    return header + bytes(body)


def test_ac3_a_wav_written_by_the_client_encoder_is_read_by_ffprobe(tmp_path):
    """AC-3: el WAV de `encodeWav` (client) lo lee ffprobe: 1,0 s, mono, 48 kHz y 24 bits.
    El client fija la huella de sus bytes; aquí se reconstruyen en Python y se comprueba que coinciden."""
    data = _client_encoder_bytes()
    assert hashlib.sha256(data).hexdigest() == FINGERPRINT.read_text(encoding='utf-8').strip()
    wav = tmp_path / 'client-sine-1s-48k-24b.wav'
    wav.write_bytes(data)
    report = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(wav)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    stream = json.loads(report.stdout)['streams'][0]

    assert ffmpeg.probe_duration(wav) == pytest.approx(1.0, abs=1e-6)
    assert (stream['codec_name'], stream['channels'], stream['sample_rate']) == ('pcm_s24le', 1, '48000')
