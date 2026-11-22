"""`subtitles.create` (spec 014, D-4): arma `subtitles.json` desde su origen.

Con `file` y `narration` transcribe el audio (con la caché de la 013) en el venv de whisper. Con `cleaner` e `import`
no transcribe. Lee `params.json` de su carpeta y deja `subtitles.json` ahí.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.common import ffmpeg as ff
from content_studio.common import process
from content_studio.db import schema
from content_studio.db.connection import connect
from content_studio.subtitles.document import save
from content_studio.subtitles.sources import from_cleaner, from_import, from_narration, from_words
from content_studio.transcription import cache, models, transcribe_main

README = 'server/data/narration/README.md'


def build_document(
    origin: str,
    *,
    source: str,
    language: str,
    script: str = '',
    words: Sequence[dict] = (),
    raw: str = '',
) -> dict[str, Any]:
    """El documento del origen: palabras con tiempos (limpiador, archivo o narración), el guion o un SRT/VTT."""
    if origin == 'cleaner':
        return from_cleaner(words, source_path=source, language=language)
    if origin == 'file':
        return from_words(words, source_path=source, kind='file', language=language)
    if origin == 'narration':
        return from_narration(script, words, source_path=source, language=language)
    if origin == 'import':
        return from_import(raw, source_path=source, language=language)
    raise ValueError(f'unknown subtitle origin: {origin}')


def _words_from_transcript(path: Path) -> list[dict]:
    """Palabras de un `transcript.json`: una lista (el limpiador) o los segmentos de whisper con sus palabras."""
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, list):
        return data
    return [word for segment in data['segments'] for word in segment['words']]


def _transcribe(source: Path, *, model: str, language: str, folder: Path) -> list[dict]:
    """Transcribe con la caché de la 013: el audio a 16 kHz mono y faster-whisper. Devuelve las palabras."""
    conn = connect(paths.db_path())
    schema.migrate(conn)
    stat = source.stat()
    key_args = (str(source), stat.st_mtime, stat.st_size, model, language)
    hit = cache.find(conn, *key_args)
    if hit is not None:
        return _words_from_transcript(Path(hit))
    json_file = cache.json_path(cache.cache_key(str(source), stat.st_mtime, model, language))
    json_file.parent.mkdir(parents=True, exist_ok=True)
    wav = folder / 'audio-16k.wav'
    ff.ffmpeg('-y', '-i', str(source), '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav))
    transcribe_main.transcribe(wav, language=language, out=json_file, model=transcribe_main._load_model(model))
    cache.store(conn, *key_args, str(json_file))
    return _words_from_transcript(json_file)


def build_parser() -> argparse.ArgumentParser:
    """Argumentos del módulo: solo la carpeta del trabajo."""
    parser = argparse.ArgumentParser(prog='content_studio.subtitles.create_main')
    parser.add_argument('--folder', required=True, help='job folder, with params.json')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: lee `params.json`, arma el documento y lo guarda como `subtitles.json`."""
    args = build_parser().parse_args(argv)
    folder = Path(args.folder)
    params = json.loads((folder / 'params.json').read_text(encoding='utf-8'))
    origin = params['origin']
    source = params.get('input', '')
    language = params.get('language', 'auto')
    if origin in ('file', 'narration'):
        process.use_venv(transcribe_main._venv(), README, module='content_studio.subtitles.create_main')
        words = _transcribe(
            Path(source), model=params.get('model', models.recommended()), language=language, folder=folder
        )
    else:
        words = _words_from_transcript(Path(source)) if origin == 'cleaner' else []
    raw = Path(source).read_text(encoding='utf-8') if origin == 'import' else ''
    doc = build_document(
        origin,
        source=params.get('source', source),
        language=language,
        script=params.get('script', ''),
        words=words,
        raw=raw,
    )
    save(doc, folder / 'subtitles.json')
    print(json.dumps({'cues': len(doc['cues'])}), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
