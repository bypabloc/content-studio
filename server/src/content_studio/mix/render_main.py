"""Entrada de `mix.render` (spec 016, D-3): lee el `mix.json` del proyecto y escribe la mezcla y su `result.json`.

Corre en el worker: ffmpeg no carga modelos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from content_studio.mix import project, render


def build_parser() -> argparse.ArgumentParser:
    """Los flags del servicio: el `mix.json` del proyecto y la carpeta del trabajo."""
    parser = argparse.ArgumentParser(prog='mix_render', description='Render a mix project into its job folder.')
    parser.add_argument('--project', required=True, help='mix.json of the project')
    parser.add_argument('--out-dir', required=True, help='output folder of the job')
    return parser


def run(doc_path: Path, out_dir: Path) -> dict[str, Any]:
    """Mezcla el proyecto y deja `mix.wav` (o `mix.mp4` con video) y `result.json` en `out_dir`."""
    doc = project.load(doc_path)
    params = doc['params']
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / ('mix.mp4' if doc['video'] else 'mix.wav')
    report = render.render(
        doc['voice'],
        doc['music'],
        out,
        regions=[tuple(region) for region in doc['regions']],
        mode=params['mode'],
        duck_db=params['duck_db'],
        ramp=params['ramp_ms'] / 1000,
        music_db=params['music_db'],
        voice_db=params['voice_db'],
        intro=params['intro'],
        outro=params['outro'],
        lufs=params['lufs'],
        video=doc['video'],
        video_mode=doc['video_mode'],
    )
    result = {**report, 'output': str(out)}
    (out_dir / 'result.json').write_text(json.dumps(result), encoding='utf-8')
    return result


def main(argv: list[str] | None = None) -> int:
    """Mezcla y deja el informe en stdout. Un error de la mezcla sale con 2 y su código en stderr."""
    args = build_parser().parse_args(argv)
    try:
        result = run(Path(args.project), Path(args.out_dir))
    except render.MixError as error:
        print(error.code, file=sys.stderr)
        return 2
    print(json.dumps(result), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
