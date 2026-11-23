"""Grafo puro de composición por pistas y transformaciones del Editor."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from content_studio.editor import expr, project, render_audio, video_transitions

# cspell:ignore setpts STARTPTS vout repeatlast cropmask colorchannelmixer: filtros y etiquetas de FFmpeg.

Doc = dict[str, Any]
PropertyExpression = Callable[[str, str], str]


@dataclass(frozen=True)
class RenderInput:
    """Una fuente de video que se agrega después del fondo sintético."""

    path: Path
    image: bool
    source: str


@dataclass(frozen=True)
class Plan:
    """Entradas visuales y filtro de composición del rango pedido."""

    inputs: list[RenderInput]
    script: str
    duration: float
    canvas: Doc


@dataclass(frozen=True)
class _Transform:
    lines: list[str]
    label: str
    x: str
    y: str


def build(
    doc: Doc,
    folder: Path,
    *,
    start: float = 0,
    end: float | None = None,
    source_sizes: dict[Path, tuple[int, int]] | None = None,
) -> Plan:
    """Construye el grafo de video por capas en el orden inferior-superior de las pistas visuales."""
    canvas = doc['canvas']
    finish = timeline_end(doc, start, end)
    duration = finish - start
    clips = visible_clips(doc, start, finish)
    sizes = source_sizes or {}
    inputs: list[RenderInput] = []
    indexes: dict[Path, int] = {}
    by_track: dict[str, list[tuple[Doc, Doc]]] = {}
    for clip, track in clips:
        by_track.setdefault(track['id'], []).append((clip, track))
        source = Path(clip['src'])
        source = source if source.is_absolute() else folder / source
        source = source.resolve()
        if source not in indexes:
            indexes[source] = len(inputs) + 1
            inputs.append(RenderInput(source, clip['media'] == 'image', clip['src']))
    lines = ['[0:v]format=rgba[base]']
    current = 'base'
    layer_index = 0
    for track in (item for item in doc.get('tracks', []) if item['id'] in by_track):
        for group in video_transitions.groups(by_track[track['id']], doc.get('transitions', []), start, finish):
            if group.transitions:
                layer = video_transitions.compose(
                    group,
                    folder,
                    indexes,
                    sizes,
                    canvas,
                    start,
                    finish,
                    f't{layer_index}',
                    _transform,
                )
                lines.extend(layer.lines)
                clip_start, clip_end = layer.start - start, layer.end - start
                label, x, y = layer.label, '0', '0'
            else:
                clip, clip_track = group.items[0]
                source = Path(clip['src'])
                source = source if source.is_absolute() else folder / source
                source = source.resolve()
                source_size = sizes.get(source)
                if source_size is None:
                    raise ValueError('unreadable_media')
                source_start, clip_start, clip_end = _range_for(clip, start, finish)
                length = clip_end - clip_start
                stream = f's{layer_index}'
                source_in = 0 if clip['media'] == 'image' else clip['src_in'] + source_start
                lines.append(
                    f'[{indexes[source]}:v]trim=start={_num(source_in)}:duration={_num(length)},'
                    f'setpts=PTS-STARTPTS+{_num(clip_start)}/TB,fps={_num(canvas["fps"])},format=rgba[{stream}]'
                )
                transformed = _transform(clip, clip_track, stream, start, source_size, f'c{layer_index}_')
                lines.extend(transformed.lines)
                label, x, y = transformed.label, transformed.x, transformed.y
            output = f'v{layer_index}'
            enable = f'gte(t,{_num(clip_start)})*lt(t,{_num(clip_end)})'
            lines.append(
                f'[{current}][{label}]overlay=x={x}:y={y}:'
                f"eval=frame:format=auto:alpha=straight:eof_action=pass:repeatlast=0:enable='{enable}'[{output}]"
            )
            current = output
            layer_index += 1
    if layer_index == 0:
        lines.append('[base]null[vout]')
    else:
        lines.append(f'[{current}]null[vout]')
    return Plan(inputs, ';\n'.join(lines) + '\n', duration, canvas)


def visible_clips(doc: Doc, start: float, end: float) -> list[tuple[Doc, Doc]]:
    """Pistas visibles en orden inferior-superior y sus clips por inicio."""
    tracks = {track['id']: track for track in doc.get('tracks', []) if track.get('kind') == 'video'}
    return [
        (clip, tracks[clip['track']])
        for track in doc.get('tracks', [])
        if track.get('kind') == 'video' and not track.get('hidden', False) and track.get('opacity', 1) > 0
        for clip in sorted(doc.get('clips', []), key=lambda item: item['start'])
        if clip['track'] == track['id'] and 'media' in clip and _overlaps(clip, start, end)
    ]


def timeline_end(doc: Doc, start: float, end: float | None) -> float:
    """Valida el rango y da un cuadro al lienzo vacío usado por la vista exacta."""
    total = project.duration(doc)
    finish = total if end is None else end
    if total == 0 and end is None and start == 0:
        finish = 1 / doc['canvas']['fps']
    if (
        not math.isfinite(start)
        or not math.isfinite(finish)
        or start < 0
        or finish <= start
        or (total > 0 and finish > total)
    ):
        raise render_audio.RenderError('bad_render_range', {'start': start, 'end': finish})
    return finish


def _transform(
    clip: Doc,
    track: Doc,
    source: str,
    start: float,
    source_size: tuple[int, int],
    namespace: str,
) -> _Transform:
    """Aplica máscara alfa, rotación con caja fija y escala animable al flujo del clip."""
    transform = clip['transform']
    frames = clip.get('keyframes', {})
    offset = clip['start'] - start
    length = project.clip_length(clip)

    def prop(key: str, variable: str = 't') -> str:
        return expr.property_expression(frames.get(key, []), length, transform[key], offset=offset, variable=variable)

    crop = transform['crop']
    crop_keys = ('crop_l', 'crop_t', 'crop_r', 'crop_b')
    crop_frames = any(frames.get(key) for key in crop_keys)
    opacity_frames = bool(frames.get('opacity'))
    source_width, source_height = source_size
    edges = {
        edge: expr.property_expression(frames.get(f'crop_{edge}', []), length, crop[edge], offset=offset)
        for edge in ('l', 't', 'r', 'b')
    }
    mask_edges = {
        edge: expr.property_expression(frames.get(f'crop_{edge}', []), length, crop[edge], offset=offset, variable='T')
        for edge in ('l', 't', 'r', 'b')
    }
    lines: list[str] = []
    current = source
    if crop_frames:
        current = _append(lines, 'cropmask', namespace)
        inside = (
            f'gte(X,W*({mask_edges["l"]}))*lt(X,W*(1-({mask_edges["r"]})))'
            f'*gte(Y,H*({mask_edges["t"]}))*lt(Y,H*(1-({mask_edges["b"]})))'
        )
        alpha = _alpha_multiplier(clip, track, offset, length, prop, crop_mask=inside)
        lines.append(f"[{source}]geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{alpha}'[{current}]")
    else:
        left, top, right, bottom = (crop[key] for key in ('l', 't', 'r', 'b'))
        if any((left, top, right, bottom)):
            current = _append(lines, 'crop', namespace)
            lines.append(
                f'[{source}]crop=w=iw*(1-{_num(left)}-{_num(right)}):h=ih*(1-{_num(top)}-{_num(bottom)}):'
                f'x=iw*{_num(left)}:y=ih*{_num(top)}[{current}]'
            )
            source_width = max(1, int(source_width * (1 - left - right)))
            source_height = max(1, int(source_height * (1 - top - bottom)))
        if opacity_frames or clip['fade_in'] > 0 or clip['fade_out'] > 0:
            next_label = _append(lines, 'alpha', namespace)
            alpha = _alpha_multiplier(clip, track, offset, length, prop)
            lines.append(f"[{current}]geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*{alpha}'[{next_label}]")
            current = next_label
        elif transform['opacity'] * track.get('opacity', 1) < 1:
            next_label = _append(lines, 'opacity', namespace)
            opacity = _num(transform['opacity'] * track.get('opacity', 1))
            lines.append(f'[{current}]colorchannelmixer=aa={opacity}[{next_label}]')
            current = next_label
    rotation = prop('rotation')
    next_label = _append(lines, 'rot', namespace)
    diagonal = math.ceil(math.hypot(source_width, source_height))
    lines.append(f"[{current}]rotate=angle='({rotation})*PI/180':ow={diagonal}:oh={diagonal}:c=black@0[{next_label}]")
    current = next_label
    scale_x, scale_y = prop('scale_x'), prop('scale_y')
    next_label = _append(lines, 'scale', namespace)
    lines.append(f"[{current}]scale=w='max(1,iw*({scale_x}))':h='max(1,ih*({scale_y}))':eval=frame[{next_label}]")
    anchor_x, anchor_y = prop('anchor_x'), prop('anchor_y')
    x, y = prop('x'), prop('y')
    if crop_frames:
        dx = f'(({edges["l"]}+({anchor_x})*(1-({edges["l"]})-({edges["r"]}))-0.5)*{source_width})'
        dy = f'(({edges["t"]}+({anchor_y})*(1-({edges["t"]})-({edges["b"]}))-0.5)*{source_height})'
    else:
        dx = f'(({anchor_x}-0.5)*{source_width})'
        dy = f'(({anchor_y}-0.5)*{source_height})'
    angle = f'(({rotation})*PI/180)'
    anchor_dx = f'(({dx})*cos({angle})-({dy})*sin({angle}))*({scale_x})'
    anchor_dy = f'(({dx})*sin({angle})+({dy})*cos({angle}))*({scale_y})'
    return _Transform(
        lines,
        next_label,
        f"'main_w/2+({x})-({anchor_dx})-overlay_w/2'",
        f"'main_h/2+({y})-({anchor_dy})-overlay_h/2'",
    )


def _alpha_multiplier(
    clip: Doc,
    track: Doc,
    offset: float,
    length: float,
    prop: PropertyExpression,
    crop_mask: str | None = None,
) -> str:
    """Combina el recorte y la opacidad de clip/pista con los fades de su rango local."""
    parts = []
    if crop_mask:
        parts.append(f'if({crop_mask},1,0)')
    parts.append(f'({prop("opacity", "T")})*{_num(track.get("opacity", 1))}')
    local = _time('T', offset)
    if clip['fade_in'] > 0:
        parts.append(f'clip(({local})/{_num(clip["fade_in"])},0,1)')
    if clip['fade_out'] > 0:
        parts.append(f'clip(({_num(length)}-({local}))/{_num(clip["fade_out"])},0,1)')
    return 'alpha(X,Y)*' + '*'.join(parts)


def _overlaps(clip: Doc, start: float, end: float) -> bool:
    return clip['start'] < end and clip['start'] + project.clip_length(clip) > start


def _range_for(clip: Doc, start: float, end: float) -> tuple[float, float, float]:
    """Desplazamiento de fuente y bordes del clip dentro del rango exportado."""
    source_start = max(0, start - clip['start'])
    clip_start = max(start, clip['start']) - start
    clip_end = min(clip['start'] + project.clip_length(clip), end) - start
    return source_start, clip_start, clip_end


def _append(lines: list[str], prefix: str, namespace: str) -> str:
    return f'{namespace}{prefix}{len(lines)}'


def _time(variable: str, offset: float) -> str:
    return f'({variable}-({_num(offset)}))'


def _num(value: float) -> str:
    """Número compacto para parámetros y expresiones de FFmpeg."""
    return format(float(value), '.12g')
