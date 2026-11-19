"""ffmpeg desde Python: salida de error (ahí escriben volumedetect, ebur128, silencedetect y loudnorm)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


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


def loudness(ruta: Path | str) -> tuple[float, float]:
    """Loudness integrada (LUFS) y pico real (dBTP) con ebur128."""
    veri = ffmpeg('-i', str(ruta), '-af', 'ebur128=peak=true', '-f', 'null', '-')
    return (
        float(re.search(r'^\s*I:\s+(-?[\d.]+) LUFS', veri, re.M)[1]),
        float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', veri)[1]),
    )
