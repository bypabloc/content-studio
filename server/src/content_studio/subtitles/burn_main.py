"""Entrada de `subtitles.burn` (spec 014, D-7): escribe el ASS del documento y quema los subtítulos en su video.

Corre en el venv principal: es ffmpeg y texto. Sale con código 3 si el ffmpeg del sistema no trae libass.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.common import ffmpeg as ff
from content_studio.subtitles import burn
from content_studio.subtitles.ass import to_ass
from content_studio.subtitles.document import load
from content_studio.subtitles.styles import PRESETS, preset
from content_studio.system import tools

NO_LIBASS = 3  # el código de salida que el servicio traduce a `ffmpeg_no_libass`


class NoLibass(Exception):
    """El ffmpeg del sistema no trae el filtro `subtitles` (libass)."""


def run(doc_path: Path, out: Path, *, preset_name: str | None = None) -> dict[str, Any]:
    """Escribe `subtitles.ass` y `subtitled.mp4` en `out` y devuelve el informe. Sin libass lanza `NoLibass`.

    Sin preset, el estilo es el del documento sobre el clásico (un documento nuevo trae el estilo vacío).
    """
    system = tools.detect()
    if not system['subtitles_filter']:
        raise NoLibass()
    doc = load(doc_path)
    source = Path(doc['source']['path'])
    width, height = ff.video_size(source)
    style = preset(preset_name) if preset_name else {**preset('classic'), **doc['style']}
    out.mkdir(parents=True, exist_ok=True)
    ass = out / 'subtitles.ass'
    ass.write_text(to_ass(doc, style, (width, height)), encoding='utf-8')
    destination = out / 'subtitled.mp4'
    burn.burn(source, ass, paths.DATA / 'fonts', destination, nvenc=system['gpu'] is not None)
    return {'video': str(destination), 'ass': str(ass), 'width': width, 'height': height}


def build_parser() -> argparse.ArgumentParser:
    """Los flags de `subtitles.burn`: el documento del proyecto, la carpeta del trabajo y el preset (opcional)."""
    parser = argparse.ArgumentParser(prog='burn_main', description='Burn the subtitles of a project into its video.')
    parser.add_argument('--doc', required=True, help='subtitles.json of the project')
    parser.add_argument('--out', required=True, help='output folder of the job')
    parser.add_argument('--preset', choices=sorted(PRESETS), help='style preset; by default, the document style')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: quema y deja el informe en stdout. Sin libass, sale con `NO_LIBASS` y lo dice en stderr."""
    args = build_parser().parse_args(argv)
    try:
        report = run(Path(args.doc), Path(args.out), preset_name=args.preset)
    except NoLibass:
        print('ffmpeg has no libass: install the full build (winget install Gyan.FFmpeg).', file=sys.stderr)
        return NO_LIBASS
    print(json.dumps(report), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
