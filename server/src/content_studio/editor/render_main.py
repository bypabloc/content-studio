"""`python -m content_studio.editor.render_main`: el trabajo `editor.render` (spec 017, D-4).

Lee el `project.json`, valida el documento y renderiza el audio a `<proyecto>/exports/<carpeta del trabajo>.<ext>`.
Deja `result.json` en la carpeta del trabajo y lo imprime. Sale con 1 si el render falla, con 2 si el documento no vale.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from content_studio.common import ffmpeg as ff
from content_studio.editor import project, render_audio, render_video, store
from content_studio.media import formats


def build_parser() -> argparse.ArgumentParser:
    """Los flags del trabajo: el proyecto, el formato, la sonoridad (opcional) y la carpeta del trabajo."""
    parser = argparse.ArgumentParser(prog='render_main')
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--format', default='wav')
    parser.add_argument('--quality', type=int)
    parser.add_argument('--normalize')
    parser.add_argument('--start', type=float)
    parser.add_argument('--end', type=float)
    parser.add_argument('--name')
    parser.add_argument('--out-dir', required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Renderiza el proyecto y deja su resultado en `result.json`. Devuelve el código de salida."""
    args = build_parser().parse_args(argv)
    project_file = args.project.resolve()
    doc, _ = store.read(project_file)
    errors = project.validate(doc)
    if errors:
        print(json.dumps({'status': 'failed', 'errors': errors}, ensure_ascii=False))
        return 2
    target = formats.TARGETS.get(args.format)
    if target is None or target['kind'] not in {'audio', 'video'}:
        print(json.dumps({'status': 'failed', 'error': 'unknown_target', 'params': {'target': args.format}}))
        return 2
    if args.quality is not None and (target['kind'] != 'video' or not 0 <= args.quality <= 51):
        print(json.dumps({'status': 'failed', 'error': 'invalid_video_quality', 'params': {'quality': args.quality}}))
        return 2
    extension = target['ext']
    exports = project_file.parent / 'exports'
    out = store.unique_export_path(exports, args.name or args.out_dir.name, extension)
    out.parent.mkdir(exist_ok=True)
    try:
        if target['kind'] == 'audio':
            render_audio.render(
                doc, project_file.parent, out, args.format, args.normalize, start=args.start or 0, end=args.end
            )
        else:
            render_video.render(
                doc,
                project_file.parent,
                out,
                args.format,
                args.normalize,
                start=args.start or 0,
                end=args.end,
                quality=args.quality,
            )
    except (render_audio.RenderError, subprocess.CalledProcessError) as error:
        failure_result = (
            {'status': 'failed', 'error': error.code, 'params': error.params}
            if isinstance(error, render_audio.RenderError)
            else {
                'status': 'failed',
                'error': str(error),
            }
        )
        (args.out_dir / 'result.json').write_text(json.dumps(failure_result, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(failure_result, ensure_ascii=False))
        if isinstance(error, render_audio.RenderError) and error.code == 'missing_source':
            return 3
        return 1
    result: dict[str, Any] = {'status': 'done', 'output': str(out), 'duration': ff.probe_duration(out)}
    (args.out_dir / 'result.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
