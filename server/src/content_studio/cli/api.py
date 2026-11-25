"""`studio api` (spec 028): arranque bajo demanda, estado, apagado y token del server compartido de la instalación."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from content_studio.db import connection, jobs, schema
from content_studio.jobs import queue
from content_studio.runtime import discovery, instance


def add_parser(sub: Any, db_flag: Callable[[], argparse.ArgumentParser]) -> None:
    """Registra `studio api` con sus acciones."""
    api_p = sub.add_parser('api', help='the shared local server: up, status, down and token')
    actions = api_p.add_subparsers(dest='api_action', required=True)
    up_p = actions.add_parser('up', parents=[db_flag()], help='start it if it is not running; print its address')
    up_p.add_argument('--with-token', action='store_true', help='also print the token (desktop app only)')
    actions.add_parser('status', parents=[db_flag()], help='address and whether it answers')
    down_p = actions.add_parser('down', parents=[db_flag()], help='stop it; refuses while a job runs')
    down_p.add_argument('--force', action='store_true', help='cancel the active jobs and stop')
    token_p = actions.add_parser('token', parents=[db_flag()], help='path of the token file (never the token)')
    token_p.add_argument('--rotate', action='store_true', help='new token; the previous one stops working')


def dispatch(args: argparse.Namespace) -> int:
    """Ejecuta la acción elegida de `studio api`."""
    if args.api_action == 'up':
        return up(args.db, with_token=args.with_token)
    if args.api_action == 'status':
        return status(args.db)
    if args.api_action == 'down':
        return down(args.db, force=args.force)
    return token(args.db, rotate=args.rotate)


def up(db: Path, with_token: bool = False) -> int:
    """Imprime la dirección del server, y lo arranca si no está vivo."""
    try:
        info = instance.ensure_running(db)
    except TimeoutError as error:
        print(str(error), file=sys.stderr)
        return 2
    if with_token:
        info = {**info, 'token': discovery.token(db.parent)}
    print(json.dumps({'ready': info}), flush=True)
    return 0


def status(db: Path) -> int:
    """La dirección anotada y si responde."""
    info = discovery.read(db.parent)
    alive = bool(info) and instance.alive(info or {}, discovery.token(db.parent))
    print(json.dumps({'alive': alive, **(info or {})}))
    return 0 if alive else 1


def down(db: Path, force: bool = False, stop: Callable[[Path], object] = instance.stop) -> int:
    """Apaga el server; con un trabajo activo se niega salvo con --force, que los cancela antes."""
    folder = db.parent
    if discovery.read(folder) is None:
        print(json.dumps({'stopped': False}))
        return 0
    conn = connection.connect(db)
    try:
        schema.migrate(conn)
        active = [job for state in ('running', 'queued') for job in jobs.list_jobs(conn, status=state)]
        if active and not force:
            print(f'{len(active)} job(s) active; use --force to cancel them and stop', file=sys.stderr)
            return 1
        for job in active:
            queue.cancel(conn, job['id'])
    finally:
        conn.close()
    stop(folder)
    print(json.dumps({'stopped': True}))
    return 0


def token(db: Path, rotate: bool = False) -> int:
    """Crea o rota el token y imprime su ruta; el token nunca se imprime."""
    discovery.token(db.parent, rotate=rotate)
    print(json.dumps({'path': str(db.parent / discovery.TOKEN)}))
    return 0
