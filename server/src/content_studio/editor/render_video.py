"""Fotograma exacto y exportación de video con el grafo puro de `video_graph`."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from content_studio.common import encode, ffmpeg
from content_studio.editor import project, render_audio
from content_studio.editor.video_graph import Plan, RenderInput, build, timeline_end, visible_clips
from content_studio.media import convert, formats, normalize
from content_studio.system import tools

# cspell:ignore lavfi vout libvpx: nombres de filtros, etiquetas y codecs de FFmpeg.


def render_frame(doc: dict[str, Any], folder: Path, time: float, output: Path) -> Path:
    """Escribe un PNG con el mismo grafo y composición que la exportación de video."""
    duration = _duration(doc)
    if time < 0 or time > duration:
        raise ValueError('unreadable_media')
    if duration == 0:
        plan = build(doc, folder)
    elif time == duration:
        plan = build({**doc, 'tracks': [], 'clips': []}, folder)
    else:
        finish = min(time + 1 / doc['canvas']['fps'], duration)
        inputs = _visual_inputs(doc, folder, time, finish)
        missing = _missing_visual_sources(inputs)
        if missing:
            raise ValueError('unreadable_media')
        plan = build(doc, folder, start=time, end=finish, source_sizes=_source_sizes(inputs))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='editor-frame-', dir=output.parent) as temporary:
        graph = Path(temporary) / 'frame.filter'
        graph.write_text(plan.script, encoding='utf-8')
        ffmpeg.ffmpeg(
            *_input_args(plan),
            '-/filter_complex',
            str(graph),
            '-map',
            '[vout]',
            '-frames:v',
            '1',
            '-c:v',
            'png',
            '-f',
            'image2',
            str(output),
        )
    if not output.is_file() or not output.stat().st_size:
        raise ValueError('unreadable_media')
    return output


def render(
    doc: dict[str, Any],
    folder: Path,
    out: Path,
    format: str = 'mp4-h264',
    normalize_preset: str | None = None,
    *,
    start: float = 0,
    end: float | None = None,
    quality: int | None = None,
) -> Path:
    """Exporta el lienzo y, si existe, el grafo de audio de la 017 en el mismo trabajo de FFmpeg."""
    target = formats.TARGETS.get(format)
    if target is None or target['kind'] != 'video':
        raise render_audio.RenderError('unknown_target', {'target': format})
    if quality is not None and (isinstance(quality, bool) or not isinstance(quality, int) or not 0 <= quality <= 51):
        raise render_audio.RenderError('invalid_video_quality', {'quality': quality})
    finish = timeline_end(doc, start, end)
    inputs = _visual_inputs(doc, folder, start, finish)
    missing = _missing_visual_sources(inputs) + _missing_audio_sources(doc, folder)
    if missing:
        raise render_audio.RenderError('missing_source', {'paths': list(dict.fromkeys(missing))})
    plan = build(doc, folder, start=start, end=end, source_sizes=_source_sizes(inputs))
    audio_plan = _audio_plan(doc, folder, start, end)
    if normalize_preset and audio_plan is None:
        raise render_audio.RenderError('nothing_to_render')
    script = plan.script
    if audio_plan is not None:
        script += ';\n' + _shift_audio_inputs(audio_plan.script, 1 + len(plan.inputs))
    args = _input_args(plan)
    if audio_plan is not None:
        for path in audio_plan.inputs:
            args.extend(['-i', str(path)])
    args += ['-/filter_complex', '']
    graph_option_index = len(args) - 1
    args += ['-map', '[vout]', '-t', _num(plan.duration)]
    if audio_plan is not None:
        args += ['-map', '[out]', *normalize.audio_args(out)]
    args += _video_codec_args(target, quality)
    args += ['-pix_fmt', 'yuv420p', '-r', _num(plan.canvas['fps']), str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    graph = _graph_path(out)
    graph.write_text(script, encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='editor-render-', dir=out.parent) as temporary:
        args[graph_option_index] = str(graph)
        if normalize_preset:
            raw = Path(temporary) / f'render{out.suffix}'
            args[-1] = str(raw)
            ffmpeg.ffmpeg('-y', *args)
            normalize.normalize(raw, out, target=normalize.target_lufs(normalize_preset))
        else:
            ffmpeg.ffmpeg('-y', *args)
    return out


def _duration(doc: dict[str, Any]) -> float:
    return project.duration(doc)


def _input_args(plan: Plan) -> list[str]:
    """Entradas FFmpeg: lienzo lavfi, imágenes en bucle y fuentes de video."""
    canvas = plan.canvas
    base_duration = plan.duration + 1 / canvas['fps']
    base = (
        f'color=c={canvas["background"]}:s={canvas["width"]}x{canvas["height"]}:'
        f'r={_num(canvas["fps"])}:d={_num(base_duration)}'
    )
    args = ['-f', 'lavfi', '-i', base]
    for item in plan.inputs:
        if item.image:
            args += ['-loop', '1', '-framerate', _num(canvas['fps'])]
        args += ['-i', str(item.path)]
    return args


def _audio_plan(doc: dict[str, Any], folder: Path, start: float, end: float | None) -> render_audio.Plan | None:
    """El audio del render de la 017; los proyectos solo visuales no agregan un stream vacío."""
    try:
        return render_audio.build(doc, folder, start=start, end=end)
    except render_audio.RenderError as error:
        if error.code == 'nothing_to_render':
            return None
        raise


def _shift_audio_inputs(script: str, offset: int) -> str:
    """Mueve los índices de entrada del grafo de audio detrás de las fuentes visuales."""
    return re.sub(r'\[(\d+):a\]', lambda match: f'[{int(match[1]) + offset}:a]', script)


def _video_codec_args(target: dict[str, Any], quality: int | None = None) -> list[str]:
    """Selecciona NVENC si está disponible; conserva una salida por software en los demás equipos."""
    codec = target['codec']
    nvenc = target.get('nvenc')
    if nvenc and tools.detect()['gpu'] is not None and nvenc in convert.available_encoders():
        if quality is not None:
            return ['-c:v', nvenc, '-preset', 'p5', '-cq', str(quality)]
        if nvenc == 'h264_nvenc':
            return encode.video_codec(True)
        return ['-c:v', nvenc, '-preset', 'p5', '-cq', '23']
    if codec == 'libx264':
        if quality is not None:
            return ['-c:v', codec, '-crf', str(quality), '-preset', 'medium']
        return encode.video_codec(False)
    if codec == 'libx265':
        return ['-c:v', codec, '-crf', str(quality if quality is not None else 23), '-preset', 'medium']
    if codec == 'libvpx-vp9':
        return ['-c:v', codec, '-crf', str(quality if quality is not None else 31), '-b:v', '0']
    if quality is not None:
        return ['-c:v', codec, '-crf', str(quality)]
    return ['-c:v', codec]


def _missing_visual_sources(inputs: list[RenderInput]) -> list[str]:
    """Fuentes visibles del rango que no existen, en orden de aparición."""
    return [item.source for item in inputs if not item.path.is_file()]


def _visual_inputs(doc: dict[str, Any], folder: Path, start: float, end: float) -> list[RenderInput]:
    """Rutas visuales activas en el rango, deduplicadas sin alterar el orden de las pistas."""
    inputs: dict[Path, RenderInput] = {}
    for clip, _ in visible_clips(doc, start, end):
        source = Path(clip['src'])
        source = source if source.is_absolute() else folder / source
        source = source.resolve()
        inputs.setdefault(source, RenderInput(source, clip['media'] == 'image', clip['src']))
    return list(inputs.values())


def _source_sizes(inputs: list[RenderInput]) -> dict[Path, tuple[int, int]]:
    """Lee las dimensiones de cada entrada para calcular el ancla tras la rotación."""
    return {item.path: ffmpeg.video_size(item.path) for item in inputs}


def _missing_audio_sources(doc: dict[str, Any], folder: Path) -> list[str]:
    """Fuentes de audio ausentes, con las rutas del proyecto para el resultado del trabajo."""
    missing = []
    for clip in doc['clips']:
        if 'media' in clip:
            continue
        path = Path(clip['src'])
        if not (path if path.is_absolute() else folder / path).is_file() and clip['src'] not in missing:
            missing.append(clip['src'])
    return missing


def _num(value: float) -> str:
    """Número compacto para parámetros de FFmpeg."""
    return format(float(value), '.12g')


def _graph_path(out: Path) -> Path:
    """Conserva el grafo del trabajo y evita pisar un filtro de un render anterior."""
    candidate = out.with_suffix('.filter')
    index = 1
    while candidate.exists():
        candidate = out.with_name(f'{out.stem}-{index}.filter')
        index += 1
    return candidate
