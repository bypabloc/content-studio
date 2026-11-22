"""`studio`: CLI headless de content-studio (spec 004, D-6): los servicios de la API, sin preguntar nada."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from contextlib import closing
from pathlib import Path

from content_studio import gpu_lock, paths
from content_studio.cli import media as media_cli
from content_studio.cli import mix as mix_cli
from content_studio.cli import serve, submit
from content_studio.common import process
from content_studio.common.checkout import main_checkout
from content_studio.db import connection, jobs, schema
from content_studio.engines import installer
from content_studio.jobs import queue
from content_studio.media.formats import is_supported
from content_studio.messages import t
from content_studio.music.parser import build_parser as music_flags
from content_studio.narration.parser import build_parser as narration_flags
from content_studio.transcription import models as whisper


def _db_flag() -> argparse.ArgumentParser:
    """`--db` también después del subcomando (PENDING 004). Sin default: si no se pasa, vale el de arriba."""
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--db', type=Path, default=argparse.SUPPRESS, help='job queue database')
    return ap


def build_parser() -> argparse.ArgumentParser:
    """Subcommands of `studio`. The narration and music flags are the ones of their services, with the same names."""
    ap = argparse.ArgumentParser(prog='studio', description='content-studio without a UI: local API, jobs and CLI.')
    ap.add_argument('--db', type=Path, default=paths.db_path(), help='job queue database')
    sub = ap.add_subparsers(dest='command', required=True, metavar='command')

    serve_p = sub.add_parser('serve', help='local API on 127.0.0.1 with the job worker')
    serve_p.add_argument('--port', type=int, default=0, help='0 picks a free port')
    serve_p.add_argument('--token', help='Bearer token; if omitted, one is generated and printed in the ready line')

    narration = sub.add_parser('narration', help='narration and voices')
    narration_cmds = narration.add_subparsers(dest='action', required=True, metavar='action')
    narration_cmds.add_parser(
        'tts', parents=[narration_flags(), _db_flag()], add_help=False, help='narrate a script (runs here)'
    )
    regenerate_p = narration_cmds.add_parser(
        'regenerate', parents=[_db_flag()], help='new take with one paragraph redone (runs here)'
    )
    regenerate_p.add_argument('job', type=int, help='a finished narration or regeneration job')
    regenerate_p.add_argument('index', type=int, help='paragraph to redo, 0-based (the first one is 0)')
    regenerate_p.add_argument('--seed', type=int, help='seed of the new paragraph; default random')
    narration_cmds.add_parser('voices', add_help=False, help='free voices: list and build (--build)')

    music_p = sub.add_parser(
        'music',
        parents=[music_flags(model_required=False), _db_flag()],
        add_help=False,
        help='instrumental music (runs here)',
    )
    music_cmds = music_p.add_subparsers(dest='music_action', metavar='action')
    samples_p = music_cmds.add_parser(
        'samples', parents=[_db_flag()], help='10 s sample of each preset, for the style browser (runs here)'
    )
    samples_p.add_argument('--styles', nargs='+', help='presets to sample (default: all)')
    samples_p.add_argument('--force', action='store_true', help='regenerate the samples that already exist')

    clean_p = sub.add_parser(
        'clean', parents=[_db_flag()], help='cut the silences of audio or video: analyze here, --auto renders too'
    )
    clean_p.add_argument('files', nargs='+', type=Path, help='audio or video files; the input is never modified')
    clean_p.add_argument(
        '--model', choices=sorted(whisper.MODELS), default=whisper.recommended(), help='faster-whisper model'
    )
    clean_p.add_argument('--language', default='auto', help='transcription language, or auto')
    clean_p.add_argument('--min-gap', type=float, default=0.5, help='silences longer than this are cut (seconds)')
    clean_p.add_argument('--padding', type=float, default=0.15, help='margin kept next to each cut (seconds)')
    clean_p.add_argument('--no-edges', action='store_true', help='keep the silence at the start and at the end')
    clean_p.add_argument('--auto', action='store_true', help='render every cut without reviewing them')
    mix_cli.add_subcommand(sub, _db_flag())
    media_cli.add_parsers(sub, _db_flag)

    jobs_p = sub.add_parser('jobs', help='the queue: list, cancel and retry jobs')
    job_cmds = jobs_p.add_subparsers(dest='action', required=True, metavar='action')
    listing = job_cmds.add_parser('list', parents=[_db_flag()], help='jobs, in queue order')
    listing.add_argument('--status')
    listing.add_argument('--kind')
    job_cmds.add_parser('cancel', parents=[_db_flag()], help='cancel a queued or running job').add_argument(
        'id', type=int
    )
    job_cmds.add_parser('retry', parents=[_db_flag()], help='new job with the same parameters').add_argument(
        'id', type=int
    )

    engines = sub.add_parser('engines', help='list, install, verify, repair and uninstall engines')
    engine_cmds = engines.add_subparsers(dest='action', required=True, metavar='action')
    engine_cmds.add_parser('list', parents=[_db_flag()], help='engines, ownership and verification status')
    for action in ('install', 'verify', 'repair', 'uninstall'):
        command = engine_cmds.add_parser(action, parents=[_db_flag()], help=f'{action} an engine')
        command.add_argument('engine', help='engine identifier from the catalog')
        if action == 'uninstall':
            command.add_argument('--force', action='store_true', help='confirm removal of the known external venv')

    sub.add_parser('openapi', help='print the API schema (OpenAPI JSON); no server and no database')
    return ap


def _voices(rest: list[str]) -> int:
    """`narration/voices` con el candado de la GPU, porque `--build` carga un motor."""
    main = main_checkout(paths.ROOT)
    gpu_lock.acquire(main, 'narration-voices', ['voices'], wait=True)
    try:
        return subprocess.call([sys.executable, '-m', 'content_studio.narration.voices.main', *rest])
    finally:
        gpu_lock.release(main)


def _jobs(args: argparse.Namespace) -> int:
    """La cola desde la base: listar, cancelar y reintentar. Un trabajo en curso lo termina su worker."""
    with closing(connection.connect(args.db)) as conn:
        schema.migrate(conn)
        if args.action == 'list':
            print(json.dumps(jobs.list_jobs(conn, kind=args.kind, status=args.status), ensure_ascii=False, indent=2))
            return 0
        if args.action == 'cancel':
            changed = queue.cancel(conn, args.id)
            print(json.dumps({'job': args.id, 'cancelled': changed}))
            return 0 if changed else 1
        try:
            new_id = queue.retry(conn, args.id)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        print(json.dumps({'job': new_id}))
        return 0


def _engines(args: argparse.Namespace) -> int:
    """Lista motores o envía la acción al servicio compartido con la API."""
    if args.action == 'list':
        with closing(connection.connect(args.db)) as conn:
            schema.migrate(conn)
            print(json.dumps(installer.list_engines(conn, paths.engines_dir(args.db)), ensure_ascii=False, indent=2))
        return 0
    if args.action == 'uninstall':
        kind = 'engine.uninstall'
    elif args.action == 'verify':
        kind = 'engine.verify'
    else:
        kind = 'engine.install'
    params = {'engine': args.engine}
    if args.action in ('install', 'repair'):
        params['repair'] = args.action == 'repair'
    elif args.action == 'uninstall':
        params['force'] = args.force
    return submit.run(kind, params, args.db, main_checkout(paths.ROOT))


def _clean(args: argparse.Namespace) -> int:
    """Analiza cada medio (GPU) y, con `--auto`, lo renderiza sin revisar. Un archivo que no sirve sale con 2 antes."""
    for path in args.files:
        if not path.is_file():
            print(t('clean.file_not_found', path=str(path)), file=sys.stderr)
            return 2
        if not is_supported(path):
            print(t('clean.unsupported_format', path=str(path)), file=sys.stderr)
            return 2
    checkout = main_checkout(paths.ROOT)
    codes = []
    for path in args.files:
        params = {
            'input': str(path),
            'model': args.model,
            'language': args.language,
            'min_gap': args.min_gap,
            'padding': args.padding,
            'edges': not args.no_edges,
        }
        analysis = submit.execute('clean.analyze', params, args.db, checkout)
        if analysis is None:
            codes.append(2)
            continue
        print(json.dumps(analysis, ensure_ascii=False))
        if analysis['status'] != 'done':
            codes.append(1)
        elif args.auto:
            render = {'input': str(path), 'analysis': analysis['output_dir']}
            codes.append(submit.run('clean.render', render, args.db, checkout))
        else:
            codes.append(0)
    return max(codes)


def _openapi() -> int:
    """El schema OpenAPI para generar los tipos del client; sin base ni puerto (la app usa una base en memoria)."""
    from content_studio.api.app import create_app  # fastapi solo aquí, como en `serve`

    # ASCII a propósito: una redirección en Windows escribe cp1252 y el JSON debe leerse igual en cualquier sistema.
    print(json.dumps(create_app(Path(':memory:'), 'openapi').openapi(), indent=2))
    return 0


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == 'serve':
        return serve.serve(args.db, main_checkout(paths.ROOT), args.port, args.token)
    if args.command == 'narration' and args.action == 'tts':
        codes = [
            submit.run('narration', params, args.db, main_checkout(paths.ROOT))
            for params in submit.split_files(submit.narration_params(args))
        ]
        return max(codes)
    if args.command == 'narration' and args.action == 'regenerate':
        return submit.run('narration.regenerate', submit.regenerate_params(args), args.db, main_checkout(paths.ROOT))
    if args.command == 'narration' and args.action == 'voices':
        return _voices(args.rest)
    if args.command == 'music' and args.music_action == 'samples':
        return submit.run('music.samples', submit.samples_params(args), args.db, main_checkout(paths.ROOT))
    if args.command == 'music':
        return submit.run('music', submit.music_params(args), args.db, main_checkout(paths.ROOT))
    if args.command == 'openapi':
        return _openapi()
    if args.command == 'engines':
        return _engines(args)
    if args.command == 'clean':
        return _clean(args)
    if args.command == 'mix':
        return mix_cli.run(args)
    if args.command in media_cli.COMMANDS:
        return media_cli.dispatch(args)
    return _jobs(args)


def main(argv: Sequence[str] | None = None) -> int:
    """Entrada de `studio`. 0 bien; 1 si el trabajo falló o no existe; 2 si el uso no es válido."""
    process.console_utf8()  # cp1252 (Windows, a una tubería) no tiene ≤ de los --help: que no reviente
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)  # `narration voices` pasa a su herramienta lo que no es de studio
    if args.command == 'narration' and args.action == 'voices':
        args.rest = extra
    elif extra:
        parser.error(f'unrecognized arguments: {" ".join(extra)}')
    try:
        return _dispatch(args)
    except submit.UsageError as error:
        parser.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
