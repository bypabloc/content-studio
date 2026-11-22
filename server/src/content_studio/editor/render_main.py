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
from content_studio.editor import project, render_audio, store
from content_studio.media import formats


def build_parser() -> argparse.ArgumentParser:
    """Los flags del trabajo: el proyecto, el formato, la sonoridad (opcional) y la carpeta del trabajo."""
    parser = argparse.ArgumentParser(prog='render_main')
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--format', default='wav')
    parser.add_argument('--normalize')
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
    extension = formats.TARGETS[args.format]['ext']
    out = project_file.parent / 'exports' / f'{args.out_dir.name}{extension}'
    out.parent.mkdir(exist_ok=True)
    try:
        render_audio.render(doc, project_file.parent, out, args.format, args.normalize)
    except (render_audio.RenderError, subprocess.CalledProcessError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}, ensure_ascii=False))
        return 1
    result: dict[str, Any] = {'status': 'done', 'output': str(out), 'duration': ff.probe_duration(out)}
    (args.out_dir / 'result.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
