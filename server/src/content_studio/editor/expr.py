"""Expresiones de FFmpeg para las curvas de keyframes compartidas."""

from __future__ import annotations

from typing import Any

from content_studio.editor import keyframes


def property_expression(
    frames: list[dict[str, Any]],
    duration: float,
    default: float,
    *,
    offset: float = 0,
    variable: str = 't',
) -> str:
    """Expresa una propiedad local del clip en el tiempo global del render."""
    segments = keyframes.segments(frames, duration)
    if not segments:
        return _num(default)
    result = _segment_expression(segments[-1], offset, variable)
    for segment in reversed(segments[:-1]):
        boundary = offset + segment[1]
        result = f'if(lt({variable},{_num(boundary)}),{_segment_expression(segment, offset, variable)},{result})'
    return result


def _segment_expression(segment: keyframes.Segment, offset: float, variable: str) -> str:
    """Expresa un tramo lineal, suave o constante de `segments()`."""
    start, end, first, last, ease = segment
    first_text, difference = _num(first), _num(last - first)
    if ease == 'hold' or start == end:
        return first_text
    time_start = offset + start
    time = f'{variable}-({_num(time_start)})' if time_start < 0 else f'{variable}-{_num(time_start)}'
    progress = f'(({time})/{_num(end - start)})'
    if ease == 'ease-in-out':
        progress = f'(3*{progress}*{progress}-2*{progress}*{progress}*{progress})'
    return f'({first_text}+{difference}*{progress})'


def _num(value: float) -> str:
    """Formato compacto y estable para literales del evaluador de FFmpeg."""
    return format(float(value), '.12g')
