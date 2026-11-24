"""`studio llm` (spec 021): las tareas del asistente desde la CLI. Solo sugieren: el resultado sale por stdout."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.cli import submit
from content_studio.common.checkout import main_checkout
from content_studio.db import connection, jobs
from content_studio.llm import models
from content_studio.messages import t


def add_subcommand(sub: argparse._SubParsersAction, db_flag: argparse.ArgumentParser) -> None:
    """`llm script-review|music-caption`."""
    parser = sub.add_parser('llm', help='local assistant (llama.cpp): suggestions as JSON, never applied')
    cmds = parser.add_subparsers(dest='llm_action', required=True, metavar='action')
    model = argparse.ArgumentParser(add_help=False)
    model.add_argument(
        '--model', choices=sorted(models.MODELS), help='LLM model; default: the chosen one or the recommended one'
    )
    review = cmds.add_parser('script-review', parents=[db_flag, model], help='review a narration script (runs here)')
    source = review.add_mutually_exclusive_group(required=True)
    source.add_argument('--text', help='script text')
    source.add_argument('--file', type=Path, help='UTF-8 text file with the script')
    review.add_argument('--all', action='store_true', help='review every paragraph, not only those with warnings')
    caption = cmds.add_parser(
        'music-caption', parents=[db_flag, model], help='Spanish description to an ACE-Step caption (runs here)'
    )
    caption.add_argument('description', help='what the music should sound like, in Spanish')


def params(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    """El tipo de trabajo y sus parámetros a partir de los flags."""
    if args.llm_action == 'script-review':
        text = args.text if args.text is not None else args.file.read_text(encoding='utf-8')
        found: dict[str, Any] = {'text': text, 'all': args.all}
        kind = 'llm.script_review'
    else:
        found, kind = {'description': args.description}, 'llm.music_caption'
    if args.model:
        found['model'] = args.model
    return kind, found


def run(args: argparse.Namespace) -> int:
    """0 con el resultado JSON; 1 si el trabajo falló (el código y su texto a stderr); 2 si el pedido no es válido."""
    kind, values = params(args)
    result = submit.execute(kind, values, args.db, main_checkout(paths.ROOT))
    if result is None:
        return 2
    if result['status'] != 'done':
        with closing(connection.connect(args.db)) as conn:
            code = (jobs.get(conn, result['job']) or {}).get('error_code') or 'process_failed'
        print(json.dumps({**result, 'error_code': code}, ensure_ascii=False))
        print(t(f'error.{code}'), file=sys.stderr)
        return 1
    print((Path(result['output_dir']) / 'result.json').read_text(encoding='utf-8'))
    return 0
