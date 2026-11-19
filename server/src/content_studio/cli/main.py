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
from content_studio.cli import serve, submit
from content_studio.common import process
from content_studio.common.checkout import main_checkout
from content_studio.db import connection, jobs, schema
from content_studio.jobs import queue
from content_studio.music.parser import build_parser as music_flags
from content_studio.narration.parser import build_parser as narration_flags


def build_parser() -> argparse.ArgumentParser:
    """Subcommands of `studio`. The narration and music flags are the ones of their services, with the same names."""
    ap = argparse.ArgumentParser(prog='studio', description='content-studio without a UI: local API, jobs and CLI.')
    ap.add_argument('--db', type=Path, default=paths.DB, help='job queue database (default var/content-studio.db)')
    sub = ap.add_subparsers(dest='command', required=True, metavar='command')

    serve_p = sub.add_parser('serve', help='local API on 127.0.0.1 with the job worker')
    serve_p.add_argument('--port', type=int, default=0, help='0 picks a free port')
    serve_p.add_argument('--token', help='Bearer token; if omitted, one is generated and printed in the ready line')

    narration = sub.add_parser('narration', help='narration and voices')
    narration_cmds = narration.add_subparsers(dest='action', required=True, metavar='action')
    narration_cmds.add_parser('tts', parents=[narration_flags()], add_help=False, help='narrate a script (runs here)')
    narration_cmds.add_parser('voices', add_help=False, help='free voices: list and build (--build)')

    sub.add_parser('music', parents=[music_flags()], add_help=False, help='instrumental music (runs here)')

    jobs_p = sub.add_parser('jobs', help='the queue: list, cancel and retry jobs')
    job_cmds = jobs_p.add_subparsers(dest='action', required=True, metavar='action')
    listing = job_cmds.add_parser('list', help='jobs, in queue order')
    listing.add_argument('--status')
    listing.add_argument('--kind')
    job_cmds.add_parser('cancel', help='cancel a queued or running job').add_argument('id', type=int)
    job_cmds.add_parser('retry', help='new job with the same parameters').add_argument('id', type=int)
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


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == 'serve':
        return serve.serve(args.db, main_checkout(paths.ROOT), args.port, args.token)
    if args.command == 'narration' and args.action == 'tts':
        return submit.run('narration', submit.narration_params(args), args.db, main_checkout(paths.ROOT))
    if args.command == 'narration' and args.action == 'voices':
        return _voices(args.rest)
    if args.command == 'music':
        return submit.run('music', submit.music_params(args), args.db, main_checkout(paths.ROOT))
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
