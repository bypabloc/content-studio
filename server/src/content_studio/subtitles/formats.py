"""Formatos SRT y VTT (spec 014, D-3): escritura desde el documento y lectura tolerante. Solo stdlib.

Al importar, las palabras de cada cue no traen tiempo propio: se reparte el del cue por caracteres.
"""

from __future__ import annotations

import re
from typing import Any

from content_studio.subtitles.segment import wrap_lines

# cspell:ignore WEBVTT: cabecera fija de VTT.
LINE_CHARS = 42
_TIME = re.compile(r'\s*(?:(\d+):)?(\d+):(\d+)[,.](\d+)')
_TAG = re.compile(r'<[^>]+>')


def _fmt(seconds: float, separator: str) -> str:
    milliseconds = round(seconds * 1000)
    hours, rest = divmod(milliseconds, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}'


def to_srt(doc: dict[str, Any]) -> str:
    """Bloques numerados con coma en los milisegundos y los renglones de hasta 42 caracteres."""
    blocks = []
    for number, cue in enumerate(doc['cues'], start=1):
        text = '\n'.join(wrap_lines(cue['text'].split(), LINE_CHARS))
        blocks.append(f'{number}\n{_fmt(cue["start"], ",")} --> {_fmt(cue["end"], ",")}\n{text}\n')
    return '\n'.join(blocks)


def to_vtt(doc: dict[str, Any]) -> str:
    """WEBVTT con punto en los milisegundos."""
    blocks = ['WEBVTT\n']
    for cue in doc['cues']:
        text = '\n'.join(wrap_lines(cue['text'].split(), LINE_CHARS))
        blocks.append(f'{_fmt(cue["start"], ".")} --> {_fmt(cue["end"], ".")}\n{text}\n')
    return '\n'.join(blocks)


def _seconds(value: str) -> float:
    match = _TIME.match(value)
    if match is None:
        raise ValueError(f'invalid subtitle time: {value!r}')
    hours, minutes, secs, fraction = match.groups()
    millis = int(fraction.ljust(3, '0')[:3])
    return (int(hours or 0) * 3600) + int(minutes) * 60 + int(secs) + millis / 1000


def _estimate_words(text: str, start: float, end: float) -> list[dict[str, Any]]:
    """Reparte el intervalo del cue entre sus palabras en proporción a sus caracteres."""
    words = text.split()
    total = sum(len(word) for word in words) or 1
    span = end - start
    result: list[dict[str, Any]] = []
    seen = 0
    for word in words:
        word_start = start + span * seen / total
        seen += len(word)
        result.append({'start': round(word_start, 6), 'end': round(start + span * seen / total, 6), 'text': word})
    if result:
        result[-1]['end'] = end
    return result


def _parse_blocks(raw: str) -> list[dict[str, Any]]:
    """Cues de un SRT o un VTT: cada bloque con una línea de tiempo «-->». Lo demás (cabecera, números,
    identificadores, etiquetas <i>) se descarta o se limpia."""
    text = raw.lstrip('﻿').replace('\r\n', '\n').replace('\r', '\n')
    cues: list[dict[str, Any]] = []
    for block in re.split(r'\n\s*\n', text.strip()):
        lines = block.split('\n')
        arrow = next((index for index, line in enumerate(lines) if '-->' in line), None)
        if arrow is None:
            continue
        left, right = lines[arrow].split('-->', 1)
        start, end = _seconds(left), _seconds(right)
        body = _TAG.sub('', ' '.join(lines[arrow + 1 :]))
        body = ' '.join(body.split())
        if body:
            cues.append({'start': start, 'end': end, 'text': body, 'words': _estimate_words(body, start, end)})
    return cues


def parse_srt(raw: str) -> list[dict[str, Any]]:
    """Cues de un SRT, con BOM, CRLF o etiquetas <i> tolerados."""
    return _parse_blocks(raw)


def parse_vtt(raw: str) -> list[dict[str, Any]]:
    """Cues de un VTT: se salta la cabecera WEBVTT y los identificadores de cue."""
    return _parse_blocks(raw)
