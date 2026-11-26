"""Transcripción con hablantes (spec 035, AC-9): transcribe_main y la diarización, cada palabra con su hablante.

Corre con el Python del server: `run` lanza transcribe_main en .venv-whisper y pyannote en .venv-diarize.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from content_studio.common import ffmpeg as ff
from content_studio.common import process, progress
from content_studio.diarization import assign, diarize_main, run
from content_studio.transcription import transcribe_main

TRANSCRIBE_SPAN = (0.0, 0.6)  # la transcripción va de 0 a 0,6 del progreso
DIARIZE_SPAN = (0.6, 0.95)  # la diarización, de 0,6 a 0,95


def build_parser() -> argparse.ArgumentParser:
    """Los flags de `transcribe_main` más los de hablantes."""
    parser = argparse.ArgumentParser(
        prog='transcribe_speakers_main', description='Transcribe and tag each word with its speaker.'
    )
    parser.add_argument('--input', required=True, help='audio or video to transcribe')
    parser.add_argument('--model', required=True, help='model from the catalog')
    parser.add_argument('--language', default='auto', help='language code, or auto to detect it')
    parser.add_argument('--out', required=True, help='output JSON with the words, their speakers and speakers.json')
    parser.add_argument('--speakers', type=int, help='exact number of speakers')
    parser.add_argument('--min-speakers', type=int, help='lowest number of speakers to look for')
    parser.add_argument('--max-speakers', type=int, help='highest number of speakers to look for')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del trabajo: transcribe, diariza y etiqueta; el JSON de palabras sale en --out."""
    args = build_parser().parse_args(argv)
    out = Path(args.out)
    folder = out.parent
    folder.mkdir(parents=True, exist_ok=True)
    wav = folder / 'audio-16k.wav'
    ff.ffmpeg('-y', '-i', args.input, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav))
    transcribe(args, out, scaled(TRANSCRIBE_SPAN))
    result = run.diarize_file(Path(args.input), wav, folder, diarize_main.speaker_counts(args), scaled(DIARIZE_SPAN))
    payload = json.loads(out.read_text(encoding='utf-8'))
    tag(payload, result['exclusive_diarization'])
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    progress.emit(1, 'transcribed')
    return 0


def transcribe(args: argparse.Namespace, out: Path, emit: Callable[[float, str], None]) -> None:
    """Corre transcribe_main en .venv-whisper y reenvía su progreso."""
    python = process.python_de(transcribe_main._venv())
    command = [
        str(python),
        '-m',
        'content_studio.transcription.transcribe_main',
        '--input',
        args.input,
        '--model',
        args.model,
        '--language',
        args.language,
        '--out',
        str(out),
    ]
    run.run_child(command, emit)


def scaled(span: tuple[float, float]) -> Callable[[float, str], None]:
    """Un emisor de progreso que lleva la fracción de una etapa (0–1) a su tramo del trabajo."""
    low, high = span

    def emit(fraction: float, stage: str) -> None:
        progress.emit(round(low + (high - low) * fraction, 4), stage)

    return emit


def tag(payload: dict[str, Any], turns: list[dict[str, Any]]) -> None:
    """Pone `speaker` en cada palabra según los turnos, y en cada segmento el hablante dominante."""
    for segment in payload['segments']:
        segment['words'] = assign.assign_speakers(segment.get('words', []), turns)
        segment['speaker'] = assign.segment_speaker(segment['words'])


if __name__ == '__main__':
    raise SystemExit(main())
