"""`studio mix` (spec 016, D-3): mezcla una voz con una música (y un video) desde la CLI.

La voz debe tener su transcripción en la caché: la deja `studio clean` sobre ella. El render es el trabajo `mix.render`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content_studio import paths
from content_studio.cli import submit
from content_studio.common.checkout import main_checkout
from content_studio.db import schema, settings
from content_studio.db.connection import connect
from content_studio.messages import t
from content_studio.mix import project
from content_studio.transcription import cache, models


def add_subcommand(sub: argparse._SubParsersAction, db_flag: argparse.ArgumentParser) -> None:
    """El subcomando `mix` con sus flags: la voz y la música, un video opcional, su modo y el ducking."""
    parser = sub.add_parser(
        'mix', parents=[db_flag], help='mix a voice over a music track (and a video); the voice must be transcribed'
    )
    parser.add_argument('--voice', required=True, type=Path, help='voice track, transcribed by studio clean first')
    parser.add_argument('--music', required=True, type=Path, help='music track; it is cut to the mix length')
    parser.add_argument('--video', type=Path, help='optional video whose audio is replaced or put under the music')
    parser.add_argument(
        '--video-mode', default='replace', choices=('replace', 'under'), help='replace the audio or mix under it'
    )
    parser.add_argument('--mode', default='transcript', choices=('transcript', 'sidechain'), help='ducking source')


def run(args: argparse.Namespace) -> int:
    """Crea el proyecto con los tramos de la transcripción en caché y lo mezcla. Sin caché, sale con 2 antes."""
    for path in (args.voice, args.music, args.video):
        if path is not None and not path.is_file():
            print(t('mix.file_not_found', path=str(path)), file=sys.stderr)
            return 2
    voice = args.voice.resolve()
    conn = connect(args.db)
    try:
        schema.migrate(conn)
        model = str(settings.get(conn, 'select.whisper.model', models.RECOMMENDED))
        hit = cache.find(conn, *project.transcript_key(voice, model))
        if hit is None:
            print(t('mix.transcript_missing', path=str(voice)), file=sys.stderr)
            return 2
        project_id = project.create(
            conn,
            args.db,
            voice=voice,
            music=args.music.resolve(),
            video=args.video.resolve() if args.video else None,
            video_mode=args.video_mode,
            regions=project.speech_regions(Path(hit), project.DEFAULT_PARAMS),
            params={'mode': args.mode},
            transcribe_job=None,
        )
        conn.commit()
    finally:
        conn.close()
    result = submit.execute('mix.render', {'mix_id': project_id}, args.db, main_checkout(paths.ROOT))
    if result is None:
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'done' else 1
