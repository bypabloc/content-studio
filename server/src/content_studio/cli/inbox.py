"""`studio inbox` (spec 030, 02 §2): registrar carpetas de entrada desde la terminal, con la base directa."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path

from content_studio.db import connection, schema
from content_studio.inbox import store
from content_studio.jobs import queue


def add_subcommand(sub: argparse._SubParsersAction, db_flag: argparse.ArgumentParser) -> None:
    """`inbox add|list|remove`."""
    parser = sub.add_parser('inbox', help='folders that process what is dropped in them: add, list, remove')
    cmds = parser.add_subparsers(dest='inbox_action', required=True, metavar='action')
    add_p = cmds.add_parser('add', parents=[db_flag], help='register a folder: each file dropped in it is processed')
    add_p.add_argument('path', type=Path, help='the folder to watch')
    add_p.add_argument('--kind', required=True, help='job kind, such as media.convert')
    add_p.add_argument('--param', action='append', default=[], metavar='KEY=VALUE', help='job parameter, repeatable')
    add_p.add_argument('--no-keep-awake', action='store_true', help='let the server sleep while this folder is idle')
    cmds.add_parser('list', parents=[db_flag], help='registered folders as JSON')
    remove_p = cmds.add_parser('remove', parents=[db_flag], help='unregister a folder; its files are not touched')
    remove_p.add_argument('folder_id', type=int, help='folder id (see inbox list)')


def _params(pairs: list[str]) -> dict:
    """Cada KEY=VALUE: el valor va como JSON si lo es (un número, una lista) y como texto si no."""
    params: dict = {}
    for pair in pairs:
        key, separator, value = pair.partition('=')
        if not separator or not key:
            raise ValueError(f'--param needs KEY=VALUE, got {pair!r}')
        try:
            params[key] = json.loads(value)
        except ValueError:
            params[key] = value
    return params


def _code(error: ValueError) -> str:
    """El código del error: el de la carpeta, o el primero de la validación del tipo."""
    if isinstance(error, queue.InvalidJob):
        return error.errors[0]['code']
    return getattr(error, 'code', str(error))


def run(args: argparse.Namespace) -> int:
    """0 bien; 1 si la carpeta a quitar no existe; 2 si el alta no pasa la validación (el código va a stderr)."""
    with closing(connection.connect(args.db)) as conn:
        schema.migrate(conn)
        if args.inbox_action == 'list':
            print(json.dumps(store.list_folders(conn), ensure_ascii=False))
            return 0
        if args.inbox_action == 'remove':
            if store.remove(conn, args.folder_id):
                return 0
            print(
                json.dumps({'code': 'inbox_folder_not_found', 'params': {'folder_id': args.folder_id}}), file=sys.stderr
            )
            return 1
        try:
            folder_id = store.register(
                conn, str(args.path), args.kind, _params(args.param), keep_awake=not args.no_keep_awake
            )
        except ValueError as error:
            print(json.dumps({'code': _code(error)}), file=sys.stderr)
            return 2
        print(json.dumps(store.get(conn, folder_id), ensure_ascii=False))
        return 0
