"""Encadenamiento de capas visuales con transiciones del Editor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from content_studio.editor import project

# cspell:ignore setpts STARTPTS xfade colorchannelmixer repeatlast: filtros de FFmpeg.

Doc = dict[str, Any]
ClipTrack = tuple[Doc, Doc]


class Transform(Protocol):
    """Resultado de las transformaciones de una capa antes de componerla."""

    lines: list[str]
    label: str
    x: str
    y: str


TransformFactory = Callable[[Doc, Doc, str, float, tuple[int, int], str], Transform]


@dataclass(frozen=True)
class Group:
    """Clips consecutivos enlazados por transiciones activas en el rango."""

    items: list[ClipTrack]
    transitions: list[Doc]


@dataclass(frozen=True)
class Layer:
    """Flujo compuesto y límites absolutos del rango visible."""

    lines: list[str]
    label: str
    start: float
    end: float


def groups(items: list[ClipTrack], transitions: list[Doc], start: float, end: float) -> list[Group]:
    """Agrupa parejas consecutivas cuya transición intersecta el rango renderizado."""
    clips = {clip['id']: clip for clip, _ in items}
    active: dict[tuple[str, str], Doc] = {}
    for transition in transitions:
        a = clips.get(transition.get('a'))
        b = clips.get(transition.get('b'))
        if a is None or b is None:
            continue
        overlap_start = b['start']
        overlap_end = a['start'] + project.clip_length(a)
        if max(start, overlap_start) < min(end, overlap_end):
            active[(a['id'], b['id'])] = transition

    result: list[Group] = []
    index = 0
    while index < len(items):
        group_items = [items[index]]
        group_transitions = []
        while index + 1 < len(items):
            pair = (items[index][0]['id'], items[index + 1][0]['id'])
            transition = active.get(pair)
            if transition is None:
                break
            group_transitions.append(transition)
            index += 1
            group_items.append(items[index])
        result.append(Group(group_items, group_transitions))
        index += 1
    return result


def compose(
    group: Group,
    folder: Path,
    indexes: dict[Path, int],
    source_sizes: dict[Path, tuple[int, int]],
    canvas: Doc,
    render_start: float,
    render_end: float,
    namespace: str,
    transform: TransformFactory,
) -> Layer:
    """Crea capas transparentes, aplica xfade y recorta al rango pedido."""
    if len(group.items) < 2 or len(group.transitions) != len(group.items) - 1:
        raise ValueError('bad_transition_group')
    lines: list[str] = []
    layers = []
    for index, (clip, track) in enumerate(group.items):
        source = Path(clip['src'])
        source = source if source.is_absolute() else folder / source
        source = source.resolve()
        source_start = 0 if clip['media'] == 'image' else clip['src_in']
        length = project.clip_length(clip)
        source_label = f'{namespace}_src{index}'
        lines.append(
            f'[{indexes[source]}:v]trim=start={_num(source_start)}:duration={_num(length)},'
            f'setpts=PTS-STARTPTS,fps={_num(canvas["fps"])},format=rgba[{source_label}]'
        )
        transformed = transform(
            clip, track, source_label, clip['start'], source_sizes[source], f'{namespace}_c{index}_'
        )
        lines.extend(transformed.lines)
        blank = f'{namespace}_blank{index}'
        layer = f'{namespace}_layer{index}'
        lines.append(
            f'color=c=black:s={canvas["width"]}x{canvas["height"]}:r={_num(canvas["fps"])}:'
            f'd={_num(length)},format=rgba,colorchannelmixer=aa=0[{blank}]'
        )
        lines.append(
            f'[{blank}][{transformed.label}]overlay=x={transformed.x}:y={transformed.y}:'
            f'eval=frame:format=auto:alpha=straight:eof_action=pass:repeatlast=0:shortest=1,'
            f'format=rgba[{layer}]'
        )
        layers.append(layer)

    current = layers[0]
    group_start = group.items[0][0]['start']
    for index, transition in enumerate(group.transitions):
        next_label = f'{namespace}_xfade{index}'
        clip = group.items[index + 1][0]
        offset = clip['start'] - group_start
        lines.append(
            f'[{current}][{layers[index + 1]}]xfade=transition={transition["type"]}:'
            f'duration={_num(transition["duration"])}:offset={_num(offset)},format=rgba[{next_label}]'
        )
        current = next_label

    group_end = group.items[-1][0]['start'] + project.clip_length(group.items[-1][0])
    visible_start = max(render_start, group_start)
    visible_end = min(render_end, group_end)
    label = f'{namespace}_range'
    lines.append(
        f'[{current}]trim=start={_num(visible_start - group_start)}:end={_num(visible_end - group_start)},'
        f'setpts=PTS-STARTPTS+{_num(visible_start - render_start)}/TB[{label}]'
    )
    return Layer(lines, label, visible_start, visible_end)


def _num(value: float) -> str:
    """Número compacto para filtros y expresiones de FFmpeg."""
    return format(float(value), '.12g')
