"""Transcribe un audio con faster-whisper y escribe las palabras con sus tiempos (spec 013, D-2).

Corre en `.venv-whisper`: `faster_whisper` se importa dentro de las funciones, así `--help` no necesita el venv.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.common import ffmpeg as ff
from content_studio.common import process
from content_studio.common import progress as progress_protocol
from content_studio.engines import recipes
from content_studio.transcription import models

README = 'server/data/narration/README.md'


def words_payload(segments: Iterable[Any], info: Any) -> dict:
    """El JSON de la transcripción: idioma, probabilidad, duración, texto plano y segmentos con sus palabras."""
    segments = list(segments)
    return {
        'language': info.language,
        'language_probability': info.language_probability,
        'duration': info.duration,
        'text': ' '.join(segment.text.strip() for segment in segments),
        'segments': [
            {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'words': [
                    {'start': w.start, 'end': w.end, 'word': w.word, 'probability': w.probability}
                    for w in (segment.words or [])
                ],
            }
            for segment in segments
        ],
    }


def progress_fraction(end: float, duration: float) -> float:
    """Fracción (0–1) del audio transcrita hasta `end`."""
    if duration <= 0:
        return 0.0
    return round(min(end / duration, 1.0), 4)


def transcribe(audio: Path, *, language: str, out: Path, model: Any, task: str = 'transcribe') -> None:
    """Transcribe `audio` con un modelo ya cargado y escribe el JSON en `out`.

    «auto» deja que el modelo detecte el idioma. `task='translate'` lo traduce al inglés (spec 014, D-8): whisper
    no da tiempos por palabra en ese modo, así que sus segmentos salen sin palabras. Emite el progreso por segmento.
    """
    segments, info = model.transcribe(
        str(audio),
        language=None if language == 'auto' else language,
        task=task,
        word_timestamps=task == 'transcribe',
        vad_filter=True,
    )
    done = []
    for segment in segments:
        done.append(segment)
        progress_protocol.emit(progress_fraction(segment.end, info.duration), 'transcribe')
    out.write_text(json.dumps(words_payload(done, info), ensure_ascii=False), encoding='utf-8')


def build_parser() -> argparse.ArgumentParser:
    """Los flags del servicio: --input, --model, --language y --out."""
    parser = argparse.ArgumentParser(prog='transcribe_main', description='Transcribe un audio con faster-whisper.')
    parser.add_argument('--input', required=True, help='audio or video to transcribe')
    parser.add_argument('--model', required=True, choices=sorted(models.MODELS), help='model from the catalog')
    parser.add_argument('--language', default='auto', help='language code, or auto to detect it')
    parser.add_argument(
        '--task', default='transcribe', choices=('transcribe', 'translate'), help='translate to English'
    )
    parser.add_argument('--out', required=True, help='output JSON with the words and their times')
    return parser


def _load_model(name: str) -> Any:
    """Carga el modelo en la GPU si el equipo tiene NVIDIA; si no, en CPU con int8."""
    from faster_whisper import WhisperModel  # solo existe en .venv-whisper

    from content_studio.system import tools

    gpu = tools.detect()['gpu'] is not None
    device, compute = ('cuda', 'int8_float16') if gpu else ('cpu', 'int8')
    return WhisperModel(models.repo(name), device=device, compute_type=compute, download_root=str(paths.models_cache()))


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: relanza en `.venv-whisper`, extrae el audio a 16 kHz mono y transcribe."""
    process.use_venv(_venv(), README, module='content_studio.transcription.transcribe_main')
    args = build_parser().parse_args(argv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = out.parent / 'audio-16k.wav'
    ff.ffmpeg('-y', '-i', args.input, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav))
    transcribe(wav, language=args.language, out=out, model=_load_model(args.model), task=args.task)
    return 0


def _venv() -> Path:
    """El venv de la receta `faster-whisper` (su carpeta la decide `paths.engine_root`)."""
    recipe = recipes.load('faster-whisper')
    return paths.engine_root(recipe.family, recipe.venv, recipe.engine) / recipe.venv


def available() -> bool:
    """¿Está instalado el venv de faster-whisper? Sin él no hay transcripción (spec 013, D-7)."""
    return _venv().is_dir()


def transcribe_text(audio: Path, *, model: str, language: str) -> str:
    """Lo que oye faster-whisper en `audio`, en texto plano. Corre el servicio en su venv: un proceso por audio."""
    from content_studio.common import process

    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder) / 'words.json'
        command = [
            sys.executable,
            '-m',
            'content_studio.transcription.transcribe_main',
            '--input',
            str(audio),
            '--model',
            model,
            '--language',
            language,
            '--out',
            str(out),
        ]
        subprocess.run(command, check=True, capture_output=True, env=process.env_src())
        return json.loads(out.read_text(encoding='utf-8'))['text']


if __name__ == '__main__':
    sys.exit(main())
