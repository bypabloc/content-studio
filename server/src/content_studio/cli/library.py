"""`studio library` (spec 020): la biblioteca desde la CLI: listar, escanear, etiquetar y mandar a la papelera."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path

from content_studio.db import connection, schema
from content_studio.library import actions, index, query, scan, tags
from content_studio.messages import t


def add_subcommand(sub: argparse._SubParsersAction, db_flag: argparse.ArgumentParser) -> None:
    """`library list|scan|tag|trash`."""
    parser = sub.add_parser('library', help='media library: list, scan watched folders, tag and trash')
    cmds = parser.add_subparsers(dest='library_action', required=True, metavar='action')
    listing = cmds.add_parser('list', parents=[db_flag], help='indexed items as JSON, newest first')
    listing.add_argument('--kind', help='narration, music, clean, convert, watched...')
    listing.add_argument('--q', help='text in the file name or the tags')
    listing.add_argument('--content', action='store_true', help='also search the scripts and transcripts on disk')
    scan_p = cmds.add_parser('scan', parents=[db_flag], help='scan the watched folders (runs here)')
    scan_p.add_argument('--add', type=Path, help='watch this folder before scanning')
    scan_p.add_argument('--folder', type=int, help='scan only this folder id')
    tag_p = cmds.add_parser('tag', parents=[db_flag], help='tag an item')
    tag_p.add_argument('item', type=int, help='item id (see library list)')
    tag_p.add_argument('name', help='tag name')
    trash_p = cmds.add_parser('trash', parents=[db_flag], help='send an indexed file to the recycle bin')
    trash_p.add_argument('target', help='item id or file path')


def _find(conn, target: str) -> int | None:  # noqa: ANN001 - conexión sqlite3
    """Id del ítem por número o por ruta."""
    if target.isdigit():
        return int(target)
    row = conn.execute('SELECT id FROM library_items WHERE path = ?', (str(Path(target).resolve()),)).fetchone()
    return row[0] if row else None


def run(args: argparse.Namespace) -> int:
    """0 bien; 1 si el ítem no existe o la ruta está protegida; 2 si la carpeta no sirve."""
    with closing(connection.connect(args.db)) as conn:
        schema.migrate(conn)
        index.backfill(conn)
        if args.library_action == 'list':
            found = query.search(conn, q=args.q, content=args.content, kind=args.kind, page_size=500)
            print(json.dumps(found['items'], ensure_ascii=False, indent=2))
            return 0
        if args.library_action == 'scan':
            if args.add is not None:
                try:
                    scan.add_folder(conn, args.add)
                except ValueError:
                    print(t('error.invalid_folder'), file=sys.stderr)
                    return 2
            print(json.dumps(scan.scan(conn, args.folder)))
            return 0
        if args.library_action == 'tag':
            try:
                print(json.dumps(tags.add(conn, args.item, args.name), ensure_ascii=False))
            except (LookupError, ValueError):
                print(t('error.item_not_found', item_id=args.item), file=sys.stderr)
                return 1
            return 0
        target = Path(args.target)
        try:
            if not args.target.isdigit():
                actions.check_unprotected(target)
            item_id = _find(conn, args.target)
            if item_id is None:
                print(t('error.item_not_found', item_id=args.target), file=sys.stderr)
                return 1
            print(json.dumps({'removed': actions.delete(conn, item_id, files=True)}))
        except actions.ProtectedPath:
            print(json.dumps({'code': 'protected_path'}))
            print(t('error.protected_path'), file=sys.stderr)
            return 1
        except LookupError:
            print(t('error.item_not_found', item_id=args.target), file=sys.stderr)
            return 1
        return 0
