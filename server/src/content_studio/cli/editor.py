"""`studio editor render` (spec 017, D-4): renderiza un proyecto del editor a un archivo de audio. Corre en la cola."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content_studio import paths
from content_studio.cli import submit
from content_studio.common.checkout import main_checkout
from content_studio.messages import t

# cspell:ignore vorbis: nombre de códec de ffmpeg (ogg-vorbis), que el diccionario no trae.


def add_subcommand(sub: argparse._SubParsersAction, db_flag: argparse.ArgumentParser) -> None:
    """El subcomando `editor` con su acción `render`: el proyecto, el formato y, opcional, la sonoridad."""
    parser = sub.add_parser('editor', help='audio projects of the editor')
    actions = parser.add_subparsers(dest='editor_action', required=True, metavar='action')
    render = actions.add_parser('render', parents=[db_flag], help='render a project to an audio file (queued)')
    render.add_argument('--project', required=True, type=Path, help='the project.json of the project')
    render.add_argument('--format', default='wav', help='wav, mp3, flac, m4a, ogg-opus or ogg-vorbis')
    render.add_argument('--normalize', choices=('podcast', 'youtube', 'broadcast'), help='loudness preset')


def run(args: argparse.Namespace) -> int:
    """Encola el render del proyecto y espera su resultado. Sin el archivo del proyecto, sale con 2."""
    project_file = args.project.resolve()
    if not project_file.is_file():
        print(t('error.editor_project_not_found', path=str(project_file)), file=sys.stderr)
        return 2
    params = {'doc': str(project_file), 'format': args.format}
    if args.normalize:
        params['normalize'] = args.normalize
    result = submit.execute('editor.render', params, args.db, main_checkout(paths.ROOT))
    if result is None:
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'done' else 1
