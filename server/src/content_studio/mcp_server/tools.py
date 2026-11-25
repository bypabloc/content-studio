"""Armado de los `params` de cada trabajo, la vista de un trabajo y sus salidas (spec 029, 02 §2).

El catálogo de herramientas está en `catalog.py`. No importa el SDK `mcp`: `sdk.py` las publica por el protocolo.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

DEFAULT_NARRATION_MODEL = 'voxcpm2'
DEFAULT_NARRATION_STYLE = 'expert'
DEFAULT_MUSIC_MODEL = 'acestep'
LIST_LIMIT = 10


class ToolError(Exception):
    """Un error de la herramienta (`isError: true`): código del catálogo de errores y sus parámetros."""

    def __init__(self, code: str, params: dict[str, Any] | None = None) -> None:
        """El código del error y sus parámetros."""
        super().__init__(code)
        self.code = code
        self.params = params or {}


def resolve_input(value: str) -> Path:
    """La ruta de un archivo que existe en el sistema (D-5); una ruta que no existe no se sigue ni se encola."""
    try:
        resolved = Path(value).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        raise ToolError('input_not_found', {'path': value}) from None
    if not resolved.is_file():
        raise ToolError('input_not_found', {'path': value})
    return resolved


def build_job(name: str, args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """El `kind` y los `params` del trabajo que crea la herramienta `name`, los mismos que arma `studio`."""
    builders = {
        'studio_narrate': _narrate,
        'studio_make_music': _music,
        'studio_transcribe': _transcribe,
        'studio_clean_silences': _clean,
        'studio_convert_media': _convert,
        'studio_submit_job': _submit,
    }
    if name not in builders:
        raise ToolError('unknown_tool', {'name': name})
    return builders[name](args)


def _narrate(args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    has_text, has_file = bool(args.get('text')), bool(args.get('script_path'))
    if has_text == has_file:  # exactamente uno: un texto o un guion
        raise ToolError('narration_source')
    params: dict[str, Any] = {
        'model': args.get('model') or DEFAULT_NARRATION_MODEL,
        'style': args.get('style') or DEFAULT_NARRATION_STYLE,
    }
    if args.get('voice'):
        params['voice'] = args['voice']
    if has_file:
        params['file'] = [str(resolve_input(args['script_path']))]
    else:
        params['text'] = args['text']
    return 'narration', params


def _music(args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not args.get('style'):
        raise ToolError('missing_style')
    params: dict[str, Any] = {'model': args.get('model') or DEFAULT_MUSIC_MODEL, 'style': list(args['style'])}
    if args.get('duration_s') is not None:
        params['duration'] = args['duration_s']
    return 'music', params


def _recommended_whisper() -> str:
    from content_studio.transcription import models as whisper

    return whisper.recommended()


def _transcribe(args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    params = {
        'input': str(resolve_input(args['input_path'])),
        'model': args.get('model') or _recommended_whisper(),
        'language': args.get('language') or 'auto',
    }
    return 'transcribe', params


def _clean(args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    params = {
        'input': str(resolve_input(args['input_path'])),
        'model': args.get('model') or _recommended_whisper(),
        'language': args.get('language') or 'auto',
    }
    return 'clean.analyze', params


def _convert(args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    params = {'input': str(resolve_input(args['input_path'])), 'target': args['target'], 'options': {}}
    return 'media.convert', params


def _submit(args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not args.get('kind'):
        raise ToolError('missing_kind')
    return str(args['kind']), dict(args.get('params') or {})


def job_view(job: dict[str, Any], outputs: list[str], waiting_on: str | None = None) -> dict[str, Any]:
    """El trabajo como `structuredContent` (02 §2): lo que el agente necesita, sin la base ni el log."""
    return {
        'job_id': job['id'],
        'kind': job['kind'],
        'status': 'waiting_gpu' if waiting_on else job['status'],
        'progress': float(job.get('progress') or 0.0),
        'stage': job.get('stage'),
        'waiting_on': waiting_on,
        'outputs': [_output(path) for path in outputs],
        'output_dir': job.get('output_dir'),
        'error': _error(job),
    }


def _error(job: dict[str, Any]) -> dict[str, str] | None:
    if not job.get('error_code'):
        return None
    return {'code': job['error_code'], 'message': job.get('error_detail') or ''}


def _mime(path: str) -> str:
    return mimetypes.guess_type(path)[0] or 'application/octet-stream'


def _output(path: str) -> dict[str, Any]:
    mime = _mime(path)
    media = mime.split('/')[0]
    return {'path': path, 'media': media if media in ('audio', 'video') else 'file', 'duration_s': None}


def resource_link(path: str) -> dict[str, str]:
    """La salida como `resource_link` file:/// (D-4): una ruta, nunca el archivo en base64."""
    resolved = Path(path).resolve()
    return {'name': resolved.name, 'uri': resolved.as_uri(), 'mime_type': _mime(path)}
