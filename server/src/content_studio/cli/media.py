"""`studio convert|normalize|trim|concat|split` (spec 015, D-6): los trabajos de ffmpeg, con los flags de su servicio.

Cada archivo es un trabajo, en su carpeta de `out/media/`; ninguno modifica su entrada. Un archivo que no existe o no es
de medios sale con 2 antes de encolar nada.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.cli import submit
from content_studio.common.checkout import main_checkout
from content_studio.media import normalize
from content_studio.media.formats import TARGETS, is_supported
from content_studio.messages import t

# Los encuadres de Redes con los valores que manda la pantalla (`convertOptions.ts`). El manual y seguir a la persona
# necesitan un rectángulo o un análisis de caras, que la CLI no hace: se usan desde la app.
REFRAMES: dict[str, dict[str, Any]] = {
    'center': {'mode': 'center'},
    'fit-bars': {'mode': 'fit-bars', 'color': 'black'},
    'fit-blur': {'mode': 'fit-blur', 'strength': 20},
}

COMMANDS = ('convert', 'normalize', 'trim', 'concat', 'split')


def add_parsers(sub: argparse._SubParsersAction, db_flag: Callable[[], argparse.ArgumentParser]) -> None:
    """Los cinco subcomandos de medios, con su `--db` después del subcomando como los demás."""
    convert_p = sub.add_parser(
        'convert', parents=[db_flag()], help='convert audio or video to a format, a social preset or a GIF'
    )
    convert_p.add_argument('files', nargs='+', type=Path, help='audio or video files; the input is never modified')
    convert_p.add_argument('--target', required=True, choices=sorted(TARGETS), help='output format')
    convert_p.add_argument(
        '--option',
        action='append',
        default=[],
        metavar='KEY=VALUE',
        help='format option: vbr=2, channels=1, sample_rate=44100, width=1080, height=1920, fps=30 (repeatable)',
    )
    convert_p.add_argument(
        '--reframe', choices=sorted(REFRAMES), help='frame for a social video (with --option width and height)'
    )

    normalize_p = sub.add_parser(
        'normalize', parents=[db_flag()], help='normalize the loudness to a preset, in two passes'
    )
    normalize_p.add_argument('files', nargs='+', type=Path, help='audio or video files; the input is never modified')
    normalize_p.add_argument(
        '--preset',
        choices=normalize.PRESETS,
        default='podcast',
        help='youtube (-14 LUFS), podcast (-16), broadcast (-23) or custom (with --target)',
    )
    normalize_p.add_argument('--target', type=float, help='custom target in LUFS, with --preset custom')
    normalize_p.add_argument('--enhance', action='store_true', help='enhance the speech before normalizing')

    trim_p = sub.add_parser('trim', parents=[db_flag()], help='keep or remove one stretch of a file, with fades')
    trim_p.add_argument('file', type=Path, help='audio or video file; the input is never modified')
    trim_p.add_argument('--start', type=float, required=True, help='start of the stretch, in seconds')
    trim_p.add_argument('--end', type=float, required=True, help='end of the stretch, in seconds')
    trim_p.add_argument('--mode', choices=('keep', 'remove'), default='keep', help='keep the stretch, or remove it')
    trim_p.add_argument('--fade-in', type=float, default=0.0, help='fade in at the start of the kept part (seconds)')
    trim_p.add_argument('--fade-out', type=float, default=0.0, help='fade out at its end (seconds)')

    concat_p = sub.add_parser('concat', parents=[db_flag()], help='join files in order, with an optional crossfade')
    concat_p.add_argument('files', nargs='+', type=Path, help='two or more files, in the order they are joined')
    concat_p.add_argument('--crossfade', type=float, default=0.0, help='seconds of crossfade between files')

    split_p = sub.add_parser('split', parents=[db_flag()], help='cut a file into parts, at markers or every N seconds')
    split_p.add_argument('file', type=Path, help='audio or video file; the input is never modified')
    cut = split_p.add_mutually_exclusive_group(required=True)
    cut.add_argument('--markers', type=float, nargs='+', help='cut times, in seconds')
    cut.add_argument('--every', type=float, help='one part every N seconds')
    split_p.add_argument(
        '--copy', action='store_true', help='copy the streams, without re-encoding (cuts on keyframes)'
    )


def _number_or_text(text: str) -> int | float | str:
    """Un valor de `--option`: entero si lo es, decimal si tiene punto, y texto en otro caso."""
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            continue
    return text


def _options(pairs: list[str]) -> dict[str, Any]:
    """`--option KEY=VALUE` repetidos a un diccionario; un par sin `=` es un uso inválido."""
    options: dict[str, Any] = {}
    for pair in pairs:
        key, separator, value = pair.partition('=')
        if not separator or not key:
            raise submit.UsageError(f'--option expects KEY=VALUE, got {pair!r}')
        options[key] = _number_or_text(value)
    return options


def _convert_params(args: argparse.Namespace, path: Path) -> dict[str, Any]:
    options = _options(args.option)
    if args.reframe is not None:
        options['reframe'] = REFRAMES[args.reframe]
    return {'input': str(path), 'target': args.target, 'options': options}


def _normalize_params(args: argparse.Namespace, path: Path) -> dict[str, Any]:
    if args.preset == 'custom' and args.target is None:
        raise submit.UsageError('--preset custom needs --target (the LUFS to aim at)')
    params: dict[str, Any] = {'input': str(path), 'preset': args.preset, 'enhance': args.enhance}
    if args.preset == 'custom':
        params['target'] = args.target
    return params


def dispatch(args: argparse.Namespace) -> int:
    """Corre el subcomando de medios. Con varios archivos, un trabajo por archivo; el código de salida es el peor."""
    files: list[Path] = args.files if args.command in ('convert', 'normalize', 'concat') else [args.file]
    for path in files:
        if not path.is_file():
            print(t('clean.file_not_found', path=str(path)), file=sys.stderr)
            return 2
        if not is_supported(path):
            print(t('clean.unsupported_format', path=str(path)), file=sys.stderr)
            return 2
    checkout = main_checkout(paths.ROOT)
    if args.command == 'concat':
        params = {'inputs': [str(path) for path in files], 'crossfade': args.crossfade}
        return submit.run('media.concat', params, args.db, checkout)
    codes = []
    for path in files:
        if args.command == 'convert':
            codes.append(submit.run('media.convert', _convert_params(args, path), args.db, checkout))
        elif args.command == 'normalize':
            codes.append(submit.run('media.normalize', _normalize_params(args, path), args.db, checkout))
        elif args.command == 'trim':
            params = {
                'input': str(path),
                'start': args.start,
                'end': args.end,
                'mode': args.mode,
                'fade_in': args.fade_in,
                'fade_out': args.fade_out,
            }
            codes.append(submit.run('media.trim', params, args.db, checkout))
        else:
            params = {'input': str(path), 'copy': args.copy}
            params.update({'markers': args.markers} if args.markers else {'every': args.every})
            codes.append(submit.run('media.split', params, args.db, checkout))
    return max(codes)
