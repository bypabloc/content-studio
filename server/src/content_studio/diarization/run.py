"""Diarizar un audio con caché y atajos (spec 035, D-7 y AC-8): pyannote solo cuando hace falta.

Stdlib en el server: pyannote corre en su venv (`run_model`); aquí solo se lee lo que deja.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from collections.abc import Callable
from pathlib import Path
from typing import Any

from content_studio.common import process, progress
from content_studio.diarization import cache, diarize_main, exports

SHORT_SECONDS = 3.0  # más corto que esto, un solo hablante (D-7)
Emit = Callable[[float, str], None]


def diarize_file(source: Path, wav: Path, out: Path, counts: dict[str, int], emit: Emit) -> dict[str, Any]:
    """Diariza `wav` (16 kHz mono de `source`) en la carpeta `out`; reusa la caché de `source` si la hay."""
    cached = cache.json_path(cache.cache_key(source, counts))
    if cached.is_file():
        result = json.loads(cached.read_text(encoding='utf-8'))
    else:
        duration = wav_seconds(wav)
        if duration < SHORT_SECONDS or counts.get('num_speakers') == 1:
            result = one_speaker(duration)
        else:
            result = run_model(wav, counts, emit)
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    exports.write_result(out, result)
    return result


def wav_seconds(path: Path) -> float:
    """Duración en segundos de un WAV."""
    with wave.open(str(path), 'rb') as handle:
        return handle.getnframes() / handle.getframerate()


def one_speaker(duration: float) -> dict[str, Any]:
    """Un solo hablante que cubre todo el audio: el atajo de los audios cortos y de num_speakers=1."""
    turn = {'start': 0.0, 'end': round(duration, 3), 'speaker': 'SPEAKER_00'}
    return {
        'duration': round(duration, 3),
        'speakers': ['SPEAKER_00'],
        'diarization': [turn],
        'exclusive_diarization': [dict(turn)],
        'embeddings': {},
    }


def run_model(wav: Path, counts: dict[str, int], emit: Emit) -> dict[str, Any]:
    """Corre diarize_main en .venv-diarize, reenvía su progreso y lee el resultado que deja en una carpeta temporal."""
    python = process.python_de(diarize_main._venv())
    with tempfile.TemporaryDirectory() as scratch:
        command = [str(python), '-m', 'content_studio.diarization.diarize_main', '--input', str(wav), '--out', scratch]
        for key, flag in diarize_main.SPEAKER_FLAGS.items():
            if key in counts:
                command += [flag, str(counts[key])]
        run_child(command, emit)
        turns = json.loads((Path(scratch) / 'turns.json').read_text(encoding='utf-8'))
        embeddings = json.loads((Path(scratch) / 'embeddings.json').read_text(encoding='utf-8'))
    return {**turns, 'embeddings': embeddings}


def run_child(command: list[str], emit: Emit) -> None:
    """Corre el proceso hijo: su @@progress va a `emit` y, si sale con error, falla con sus últimas líneas."""
    child = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=process.env_src(),
    )
    tail: list[str] = []
    assert child.stdout is not None
    for line in child.stdout:
        parsed = progress.parse(line)
        if parsed is not None:
            emit(float(parsed['p']), str(parsed.get('stage', '')))
        else:
            tail = [*tail[-19:], line.rstrip()]
    if child.wait() != 0:
        raise RuntimeError('\n'.join(tail) or 'pyannote failed')
