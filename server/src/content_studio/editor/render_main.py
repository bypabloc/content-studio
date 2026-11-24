"""`python -m content_studio.editor.render_main`: el trabajo `editor.render` (spec 017, D-4).

Lee el `project.json`, valida el documento y renderiza el audio a `<proyecto>/exports/<carpeta del trabajo>.<ext>`.
Deja `result.json` en la carpeta del trabajo y lo imprime. Sale con 1 si el render falla, con 2 si el documento no vale.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.common import ffmpeg as ff
from content_studio.db.connection import connect
from content_studio.editor import project, render_audio, render_video, store, subtitle_projects
from content_studio.media import formats
from content_studio.subtitles import export as subtitle_export


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
    parser.add_argument('--subtitle-mode', choices=('none', 'burn', 'srt', 'vtt'), default='none')
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
    if target['kind'] != 'video' and args.subtitle_mode != 'none':
        print(json.dumps({'status': 'failed', 'error': 'subtitle_mode_requires_video', 'params': {}}))
        return 2
    extension = target['ext']
    exports = project_file.parent / 'exports'
    out = store.unique_export_path(exports, args.name or args.out_dir.name, extension)
    out.parent.mkdir(exist_ok=True)
    try:
        subtitle_documents = _load_subtitle_documents(doc) if args.subtitle_mode != 'none' else {}
        if args.subtitle_mode in {'srt', 'vtt'} and not subtitle_documents:
            raise render_audio.RenderError('subtitle_track_required')
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
                subtitle_documents=subtitle_documents,
                burn_subtitles=args.subtitle_mode == 'burn',
            )
        subtitle_outputs = _write_subtitle_sidecars(doc, subtitle_documents, out, args.subtitle_mode)
    except subtitle_projects.MissingSubtitleProject as error:
        failure_result = {
            'status': 'failed',
            'error': 'subtitle_project_not_found',
            'params': {'project_id': error.project_id},
        }
        (args.out_dir / 'result.json').write_text(json.dumps(failure_result, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(failure_result, ensure_ascii=False))
        return 1
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
    if subtitle_outputs:
        result['subtitle_outputs'] = subtitle_outputs
    (args.out_dir / 'result.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _load_subtitle_documents(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Resuelve los IDs de pista contra SQLite y carga los JSON de la 014."""
    if not any(track.get('kind') == 'subtitles' for track in doc.get('tracks', [])):
        return {}
    with closing(connect(paths.db_path())) as conn:
        return subtitle_projects.load_documents(doc, conn)


def _write_subtitle_sidecars(
    doc: dict[str, Any],
    subtitle_documents: dict[str, dict[str, Any]],
    video: Path,
    mode: str,
) -> list[str]:
    """Exporta los documentos elegidos como archivos SRT o VTT junto al video."""
    if mode not in {'srt', 'vtt'}:
        return []
    tracks = [track for track in doc.get('tracks', []) if track.get('kind') == 'subtitles']
    outputs = []
    for index, track in enumerate(tracks):
        project_id = str(track['subtitles_project'])
        document = subtitle_documents[project_id]
        suffix = f'-{index + 1}' if len(tracks) > 1 else ''
        target = video.with_name(f'{video.stem}{suffix}.{mode}')
        target.write_text(
            subtitle_export.render(document, mode, (doc['canvas']['width'], doc['canvas']['height'])),
            encoding='utf-8',
        )
        outputs.append(str(target))
    return outputs


if __name__ == '__main__':
    sys.exit(main())
