"""Exportaciones del limpiador: transcripción, SRT, EDL, XML e informe (spec 013, D-5). Puras, solo stdlib."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from collections.abc import Sequence

from content_studio.clean.plan import Cut, remap

SRT_LINE_CHARS = 42
SRT_MAX_LINES = 2
SRT_MAX_SECONDS = 7.0


def transcript_txt(segments: Sequence[dict]) -> str:
    """Un renglón por segmento transcrito."""
    return ''.join(f'{segment["text"].strip()}\n' for segment in segments)


def transcript_json(words: Sequence[dict], cuts: Sequence[Cut]) -> list[dict]:
    """Las palabras con sus tiempos reasignados al limpio."""
    return [
        {'word': w['word'], 'start': round(remap(w['start'], cuts), 6), 'end': round(remap(w['end'], cuts), 6)}
        for w in words
    ]


def _wrap(words: Sequence[str]) -> list[str]:
    """Parte las palabras en renglones de hasta 42 caracteres, sin cortar palabras."""
    lines: list[str] = []
    line = ''
    for word in words:
        candidate = f'{line} {word}' if line else word
        if len(candidate) <= SRT_LINE_CHARS or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, rest = divmod(milliseconds, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, ms = divmod(rest, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}'


def srt(words: Sequence[dict], cuts: Sequence[Cut]) -> str:
    """Subtítulos del limpio: bloques de hasta 2 renglones de 42 caracteres y 7 s."""
    timed = [(w['word'], remap(w['start'], cuts), remap(w['end'], cuts)) for w in words]
    blocks: list[list[tuple[str, float, float]]] = []
    for item in timed:
        if blocks:
            current = blocks[-1] + [item]
            span = current[-1][2] - current[0][1]
            if len(_wrap([text for text, _, _ in current])) <= SRT_MAX_LINES and span <= SRT_MAX_SECONDS:
                blocks[-1] = current
                continue
        blocks.append([item])
    parts: list[str] = []
    for number, block in enumerate(blocks, start=1):
        text = '\n'.join(_wrap([word for word, _, _ in block]))
        parts.append(f'{number}\n{_srt_time(block[0][1])} --> {_srt_time(block[-1][2])}\n{text}\n')
    return '\n'.join(parts)


def _frame(seconds: float, fps: float) -> int:
    return math.floor(seconds * fps + 0.5)


def _timecode(frames: int, fps: float) -> str:
    base = round(fps)
    total_seconds, ff = divmod(frames, base)
    hours, rest = divmod(total_seconds, 3600)
    minutes, ss = divmod(rest, 60)
    return f'{hours:02d}:{minutes:02d}:{ss:02d}:{ff:02d}'


def edl(keep: Sequence[tuple[float, float]], fps: float, title: str = 'content-studio clean') -> str:
    """EDL CMX3600 con un evento por tramo a conservar.

    Los límites del limpio se acumulan en segundos y se redondean al cuadro una sola vez, así los eventos
    suman la duración sin deriva.
    """
    lines = [f'TITLE: {title}', 'FCM: NON-DROP FRAME']
    clean = 0.0
    for number, (start, end) in enumerate(keep, start=1):
        rec_in, clean = clean, clean + (end - start)
        lines.append(
            f'{number:03d}  AX       AA/V  C        '
            f'{_timecode(_frame(start, fps), fps)} {_timecode(_frame(end, fps), fps)} '
            f'{_timecode(_frame(rec_in, fps), fps)} {_timecode(_frame(clean, fps), fps)}'
        )
    return '\n'.join(lines) + '\n'


def xml_sequence(keep: Sequence[tuple[float, float]], fps: float, media_path: str, name: str, duration: float) -> str:
    """Secuencia xmeml v5 con un clipitem por tramo sobre el archivo original."""
    root = ET.Element('xmeml', version='5')
    sequence = ET.SubElement(root, 'sequence')
    ET.SubElement(sequence, 'name').text = name
    ET.SubElement(sequence, 'duration').text = str(_frame(sum(e - s for s, e in keep), fps))
    rate = ET.SubElement(sequence, 'rate')
    ET.SubElement(rate, 'timebase').text = str(round(fps))
    ET.SubElement(rate, 'ntsc').text = 'FALSE'
    track = ET.SubElement(ET.SubElement(ET.SubElement(sequence, 'media'), 'video'), 'track')
    pathurl = 'file:///' + media_path.replace('\\', '/').lstrip('/')
    clean = 0.0
    for number, (start, end) in enumerate(keep, start=1):
        rec_start, clean = clean, clean + (end - start)
        clip = ET.SubElement(track, 'clipitem', id=f'clip-{number}')
        ET.SubElement(clip, 'name').text = f'{name} {number}'
        ET.SubElement(clip, 'duration').text = str(_frame(duration, fps))
        ET.SubElement(clip, 'start').text = str(_frame(rec_start, fps))
        ET.SubElement(clip, 'end').text = str(_frame(clean, fps))
        ET.SubElement(clip, 'in').text = str(_frame(start, fps))
        ET.SubElement(clip, 'out').text = str(_frame(end, fps))
        file_el = ET.SubElement(clip, 'file', id='file-1')
        ET.SubElement(file_el, 'name').text = media_path.replace('\\', '/').rsplit('/', 1)[-1]
        ET.SubElement(file_el, 'pathurl').text = pathurl
    return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + ET.tostring(root, encoding='unicode') + '\n'


def report(
    duration_before: float,
    keep: Sequence[tuple[float, float]],
    cuts: Sequence[Cut],
    model: str,
    language: str,
    process_seconds: float,
) -> dict[str, object]:
    """Informe del limpio: duraciones, lo cortado, cortes, modelo, idioma y tiempo de proceso."""
    after = round(sum(e - s for s, e in keep), 3)
    removed = round(duration_before - after, 3)
    return {
        'duration_before': duration_before,
        'duration_after': after,
        'removed_seconds': removed,
        'removed_percent': round(removed / duration_before * 100, 1) if duration_before else 0.0,
        'cuts': sum(1 for cut in cuts if cut['enabled']),
        'model': model,
        'language': language,
        'process_seconds': round(process_seconds, 2),
    }
