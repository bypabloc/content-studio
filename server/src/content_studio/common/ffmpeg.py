"""ffmpeg desde Python: salida de error (ahí escriben volumedetect, ebur128, silencedetect y loudnorm), y picos."""

from __future__ import annotations

import json
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


PEAK_FLOOR_DBFS = -120.0  # ffmpeg escribe -inf para un silencio; JSON no admite infinitos, así que se usa este piso


def parse_loudness(verify: str) -> tuple[float, float]:
    """LUFS integrados y pico real (dBTP) de la salida de ebur128. Un silencio da el piso de -120 dBFS; si la salida no
    trae el resumen, ValueError."""
    lufs = re.search(r'^\s*I:\s+(-?[\d.]+) LUFS', verify, re.M)
    peak = re.search(r'Peak:\s+(-?inf|-?[\d.]+) dBFS', verify)
    if lufs is None or peak is None:
        raise ValueError('ffmpeg printed no loudness summary')
    return float(lufs[1]), (PEAK_FLOOR_DBFS if peak[1].endswith('inf') else float(peak[1]))


def loudness(path: Path | str) -> tuple[float, float]:
    """Loudness integrada (LUFS) y pico real (dBTP) con ebur128."""
    return parse_loudness(ffmpeg('-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'))


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
    """Pico absoluto de cada una de n ventanas contiguas que cubren todo el audio, entre 0 y 1. Siempre devuelve n
    valores, y ninguna ventana queda vacía si hay al menos n muestras.

    >>> window_peaks(array('h', [0, 16384, 0, 0]), 2)
    [0.5, 0.0]
    """
    bounds = [-(-i * len(samples) // n) for i in range(n + 1)]  # ceil(i * largo / n): los bordes no dejan huecos
    return [max((abs(x) for x in samples[bounds[i] : bounds[i + 1]]), default=0) / 32768 for i in range(n)]


def peaks(path: Path | str, n: int) -> list[float]:
    """n picos del audio, entre 0 y 1, para dibujar su forma de onda."""
    samples = array('h')
    samples.frombytes(subprocess.run(peaks_command(path), capture_output=True, check=True).stdout)
    if sys.byteorder == 'big':
        samples.byteswap()
    return window_peaks(samples, n)
