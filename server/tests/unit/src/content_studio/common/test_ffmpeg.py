"""Comandos de ffmpeg y ffprobe que arma common/ffmpeg.py, y los picos de una señal (spec 006, AC-4)."""

from __future__ import annotations

from array import array

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
