"""ffmpeg desde Python: salida de error (ahí escriben volumedetect, ebur128, silencedetect y loudnorm), y picos."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from array import array
from pathlib import Path

# cspell:ignore frombytes byteswap: métodos de array de la stdlib, que el diccionario no trae.
# cspell:ignore astats: filtro de ffmpeg que mide el nivel RMS de la sala.


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


def frame_rate(path: Path | str) -> str:
    """Tasa de cuadros del primer video del archivo, como fracción de ffprobe (por ejemplo, '30/1')."""
    return subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
         '-of', 'default=nw=1:nk=1', str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()  # fmt: skip


def peak_dbfs(path: Path | str) -> float:
    """Pico de muestra del audio en dBFS (volumedetect); un silencio da el piso de -120 dBFS."""
    found = re.search(
        r'max_volume: (-?inf|-?[\d.]+) dB', ffmpeg('-i', str(path), '-af', 'volumedetect', '-f', 'null', '-')
    )
    if found is None:
        raise ValueError('ffmpeg printed no volume summary')
    return PEAK_FLOOR_DBFS if found[1].endswith('inf') else float(found[1])


def room_tone_dbfs(path: Path | str, seconds: float = 0.3) -> float:
    """Nivel RMS en dBFS de los primeros `seconds` del audio: el ruido de la sala antes de hablar."""
    levels = re.findall(
        r'RMS level dB: (-?inf|-?[\d.]+)',
        ffmpeg('-t', str(seconds), '-i', str(path), '-af', 'astats', '-f', 'null', '-'),
    )
    if not levels:
        raise ValueError('ffmpeg printed no level summary')
    return PEAK_FLOOR_DBFS if levels[-1].endswith('inf') else float(levels[-1])


def silences(path: Path | str, noise_db: float = -50.0, minimum: float = 0.1) -> list[tuple[float, float | None]]:
    """Silencios (inicio, fin) según silencedetect; el fin es None si el silencio llega al final del audio."""
    spans: list[list] = []
    report = ffmpeg('-i', str(path), '-af', f'silencedetect=noise={noise_db}dB:d={minimum}', '-f', 'null', '-')
    for line in report.splitlines():
        if start := re.search(r'silence_start: (-?[\d.]+)', line):
            spans.append([float(start[1]), None])
        elif (end := re.search(r'silence_end: (-?[\d.]+)', line)) and spans:
            spans[-1][1] = float(end[1])
    return [(start, end) for start, end in spans]


def extract_wav(source: Path | str, start: float, end: float, destination: Path | str) -> None:
    """Extrae el tramo [start, end) de un audio o un video a WAV mono de 48 kHz y 24 bits, sin video."""
    args = ['-y', '-i', str(source), '-ss', str(start), '-t', str(end - start)]
    ffmpeg(*args, '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(destination))


def resample(source: Path | str, destination: Path | str) -> None:
    """Pasa un WAV a 48 kHz, mono y 24 bits con el conversor soxr de ffmpeg (para un micrófono que no da 48 kHz)."""
    # cspell:ignore resampler soxr
    args = ['-y', '-i', str(source), '-vn', '-af', 'aresample=resampler=soxr', '-ar', '48000', '-ac', '1']
    ffmpeg(*args, '-c:a', 'pcm_s24le', str(destination))


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
