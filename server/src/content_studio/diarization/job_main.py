"""Trabajos `diarize` y `diarize.split` (spec 035, AC-5 y AC-7): ffmpeg y la caché aquí; pyannote solo en su venv.

Corre con el Python del server: `run.diarize_file` lanza pyannote en `.venv-diarize` cuando hace falta.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from content_studio.common import ffmpeg as ff
from content_studio.common import process, progress
from content_studio.diarization import diarize_main, run, speaker_audio


def build_parser() -> argparse.ArgumentParser:
    """Dos acciones: `diarize` (turnos del audio) y `split` (un WAV por hablante)."""
    parser = argparse.ArgumentParser(prog='job_main', description='Diarize an audio file or split it per speaker.')
    sub = parser.add_subparsers(dest='action', required=True, metavar='action')
    diarize_p = sub.add_parser('diarize', help='turns, RTTM, CSV, speakers and embeddings of an audio file')
    diarize_p.add_argument('--input', required=True, help='audio or video to diarize')
    diarize_p.add_argument('--out', required=True, help='job folder')
    diarize_p.add_argument('--speakers', type=int, help='exact number of speakers')
    diarize_p.add_argument('--min-speakers', type=int, help='lowest number of speakers to look for')
    diarize_p.add_argument('--max-speakers', type=int, help='highest number of speakers to look for')
    split_p = sub.add_parser('split', help='one WAV per speaker, silent outside its turns')
    split_p.add_argument('--input', required=True, help='audio or video that was diarized')
    split_p.add_argument('--turns', required=True, help='folder with the turns.json of the diarization')
    split_p.add_argument('--out', required=True, help='job folder')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del trabajo: la acción `diarize` o `split`."""
    args = build_parser().parse_args(argv)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    if args.action == 'diarize':
        return diarize(args)
    return split(args)


def diarize(args: argparse.Namespace) -> int:
    """Audio a 16 kHz mono con ffmpeg y diarización (caché y atajos incluidos)."""
    wav = Path(args.out) / 'audio-16k.wav'
    ff.ffmpeg('-y', '-i', args.input, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav))
    run.diarize_file(Path(args.input), wav, Path(args.out), diarize_main.speaker_counts(args), emit=progress.emit)
    progress.emit(1, 'diarized')
    return 0


def split(args: argparse.Namespace) -> int:
    """Un WAV por hablante con ffmpeg, usando sus turnos exclusivos: en cada instante suena un solo hablante."""
    turns = json.loads((Path(args.turns) / 'turns.json').read_text(encoding='utf-8'))
    folder = Path(args.out) / 'speakers'
    folder.mkdir(parents=True, exist_ok=True)
    speakers = turns['speakers']
    for index, speaker in enumerate(speakers, start=1):
        command = speaker_audio.split_command(
            Path(args.input), turns['exclusive_diarization'], speaker, folder / f'{speaker}.wav'
        )
        subprocess.run(command, check=True, capture_output=True, env=process.env_src())
        progress.emit(index / len(speakers), 'splitting')
    return 0
