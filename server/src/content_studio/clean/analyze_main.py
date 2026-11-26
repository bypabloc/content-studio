"""Análisis del limpiador (spec 013, D-4): transcribe con la caché y escribe `cuts.json` en la carpeta del trabajo.

El transcriptor es una función inyectada: en la app, faster-whisper en `.venv-whisper`; en las pruebas, un simulado.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from content_studio import paths
from content_studio.clean import cuts
from content_studio.clean.plan import plan
from content_studio.common import ffmpeg as ff
from content_studio.common import process, progress
from content_studio.db import schema
from content_studio.db.connection import connect
from content_studio.diarization.run import diarize_file
from content_studio.transcription import cache, models, transcribe_main

Transcribe = Callable[[Path, Path], None]
Diarize = Callable[[Path, Path], None]  # (audio original, carpeta de la diarización): deja turns.json
README = 'server/data/narration/README.md'


def run(
    conn: sqlite3.Connection,
    source: Path,
    *,
    model: str,
    language: str,
    params: dict,
    folder: Path,
    transcribe: Transcribe,
    silences: Sequence[tuple[float, float | None]] = (),
    diarize: Diarize | None = None,
) -> dict:
    """Transcribe `source` (o usa la caché), calcula los cortes y los guarda en `folder/cuts.json`.

    `silences` son los silencios audibles del audio (inicio, fin); un fin None llega al final del audio."""
    stat = source.stat()
    key_args = (str(source), stat.st_mtime, stat.st_size, model, language)
    hit = cache.find(conn, *key_args)
    if hit is None:
        json_file = cache.json_path(cache.cache_key(str(source), stat.st_mtime, model, language))
        json_file.parent.mkdir(parents=True, exist_ok=True)
        transcribe(source, json_file)
        cache.store(conn, *key_args, str(json_file))
        json_path = str(json_file)
    else:
        json_path = hit
    transcript = json.loads(Path(json_path).read_text(encoding='utf-8'))
    words = [word for segment in transcript['segments'] for word in segment['words']]
    duration = transcript['duration']
    audible = [(start, duration if end is None else end) for start, end in silences]
    found = plan(
        words,
        duration,
        min_gap=params['min_gap'],
        padding=params['padding'],
        edges=params['edges'],
        silences=audible,
    )
    document = {
        'params': params,
        'model': model,
        'language': transcript['language'],
        'duration': duration,
        'transcript': json_path,
        'silences': [list(span) for span in audible],
        'cuts': found,
    }
    if diarize is not None and params.get('diarize'):
        turns_dir = folder / 'diarization'
        diarize(source, turns_dir)
        document['diarization'] = str(turns_dir / 'turns.json')
    cuts.save(folder, document)
    return {'cuts': len(found), 'duration': duration, 'cached': hit is not None}


def _wav16(source: Path, folder: Path) -> Path:
    """El audio de 16 kHz mono de `source` en la carpeta del trabajo; se extrae una vez."""
    wav = folder / 'audio-16k.wav'
    if not wav.exists():
        ff.ffmpeg('-y', '-i', str(source), '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav))
    return wav


def _transcriber(model: str, language: str, folder: Path) -> Transcribe:
    """El transcriptor real: extrae el audio a 16 kHz mono y lo transcribe con faster-whisper."""

    def transcribe_source(source: Path, json_file: Path) -> None:
        transcribe_main.transcribe(
            _wav16(source, folder), language=language, out=json_file, model=transcribe_main._load_model(model)
        )

    return transcribe_source


def _turns_of(folder: Path) -> Diarize:
    """La diarización real: el mismo audio de 16 kHz y `diarize_file`, que reusa su caché por archivo."""

    def find_turns(source: Path, out: Path) -> None:
        diarize_file(source, _wav16(source, folder), out, {}, progress.emit)

    return find_turns


def build_parser() -> argparse.ArgumentParser:
    """Los flags del servicio `clean.analyze`."""
    parser = argparse.ArgumentParser(prog='analyze_main', description='Find the silences to cut in a media file.')
    parser.add_argument('--input', required=True, help='audio or video to analyze')
    parser.add_argument('--model', required=True, choices=sorted(models.MODELS))
    parser.add_argument('--language', default='auto', help='language code, or auto to detect it')
    parser.add_argument('--min-gap', type=float, default=0.5, help='silences longer than this are cut (seconds)')
    parser.add_argument('--padding', type=float, default=0.15, help='margin kept on each side of a cut (seconds)')
    edges = parser.add_mutually_exclusive_group()
    edges.add_argument('--edges', dest='edges', action='store_true', default=True, help='cut the start and the end')
    edges.add_argument('--no-edges', dest='edges', action='store_false', help='keep the start and the end')
    parser.add_argument('--diarize', action='store_true', help='identify the speakers (pyannote) and keep their turns')
    parser.add_argument('--folder', required=True, help='job folder where cuts.json goes')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: parsea los flags y se relanza en `.venv-whisper` para transcribir."""
    args = build_parser().parse_args(argv)
    process.use_venv(transcribe_main._venv(), README, module='content_studio.clean.analyze_main')
    folder = Path(args.folder)
    folder.mkdir(parents=True, exist_ok=True)
    conn = connect(paths.db_path())
    schema.migrate(conn)
    params = {'min_gap': args.min_gap, 'padding': args.padding, 'edges': args.edges}
    if args.diarize:
        params['diarize'] = True
    result = run(
        conn,
        Path(args.input),
        model=args.model,
        language=args.language,
        params=params,
        folder=folder,
        transcribe=_transcriber(args.model, args.language, folder),
        silences=ff.silences(Path(args.input)),
        diarize=_turns_of(folder) if args.diarize else None,
    )
    print(json.dumps(result), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
