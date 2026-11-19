"""ffmpeg desde Python: salida de error (ahí escriben volumedetect, ebur128, silencedetect y loudnorm), y picos."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from array import array
from pathlib import Path

# cspell:ignore frombytes byteswap: métodos de array de la stdlib, que el diccionario no trae.


def ffmpeg(*args: str) -> str:
    """Corre ffmpeg (falla si sale con error) y devuelve su stderr."""
    return subprocess.run(
        ['ffmpeg', '-hide_banner', '-nostats', *args], capture_output=True, text=True, check=True
    ).stderr


def json_loudnorm(stderr: str) -> dict:
    r"""loudnorm con print_format=json escribe su JSON al final de stderr.

    >>> json_loudnorm('[Parsed_loudnorm_0] {"a": 1}\n{\n "input_i" : "-20.1"\n}\n')
    {'input_i': '-20.1'}
    """
    return json.loads(stderr[stderr.rindex('{', 0, stderr.rindex('}')) : stderr.rindex('}') + 1])


def loudness(path: Path | str) -> tuple[float, float]:
    """Loudness integrada (LUFS) y pico real (dBTP) con ebur128."""
    verify = ffmpeg('-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-')
    return (
        float(re.search(r'^\s*I:\s+(-?[\d.]+) LUFS', verify, re.M)[1]),
        float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', verify)[1]),
    )


def probe_command(path: Path | str) -> list[str]:
    """ffprobe que da la duración del archivo, en segundos, y nada más."""
    return ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)]


def probe_duration(path: Path | str) -> float:
    """Duración del archivo en segundos."""
    return float(subprocess.run(probe_command(path), capture_output=True, text=True, check=True).stdout)


def peaks_command(path: Path | str) -> list[str]:
    """ffmpeg que decodifica el audio a mono de 8 kHz, en s16le, hacia la salida estándar."""
    return ['ffmpeg', '-v', 'error', '-i', str(path), '-f', 's16le', '-ac', '1', '-ar', '8000', '-']


def window_peaks(samples: array, n: int) -> list[float]:
    """Pico absoluto de cada una de n ventanas de igual largo, entre 0 y 1. Siempre devuelve n valores.

    >>> window_peaks(array('h', [0, 16384, 0, 0]), 2)
    [0.5, 0.0]
    """
    size = max(1, math.ceil(len(samples) / n))
    return [max((abs(x) for x in samples[i * size : (i + 1) * size]), default=0) / 32768 for i in range(n)]


def peaks(path: Path | str, n: int) -> list[float]:
    """n picos del audio, entre 0 y 1, para dibujar su forma de onda."""
    samples = array('h')
    samples.frombytes(subprocess.run(peaks_command(path), capture_output=True, check=True).stdout)
    if sys.byteorder == 'big':
        samples.byteswap()
    return window_peaks(samples, n)
