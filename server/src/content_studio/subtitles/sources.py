"""Orígenes de subtítulos (spec 014, D-4): de palabras con tiempos a documento, y la alineación del guion. Puro.

La transcripción llega ya hecha (faster-whisper); este módulo no carga modelos. Solo stdlib.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from collections.abc import Sequence
from typing import Any

from content_studio.subtitles.document import new_document
from content_studio.subtitles.formats import parse_srt, parse_vtt
from content_studio.subtitles.segment import segment

# cspell:ignore WEBVTT: cabecera fija de VTT.
_NON_WORD = re.compile(r'\W')
TRAILING_WORD_SECONDS = 0.3  # palabra del guion sin par al final: se le da este tiempo


def _norm(word: str) -> str:
    """Minúsculas, sin tildes y sin signos: «¡Está!» y «esta» son lo mismo."""
    decomposed = unicodedata.normalize('NFKD', word.lower())
    plain = ''.join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _NON_WORD.sub('', plain)


def _split_by_chars(words: Sequence[str], start: float, end: float) -> list[tuple[float, float]]:
    """Reparte [start, end] entre palabras en proporción a sus caracteres."""
    weights = [len(_norm(word)) or 1 for word in words]
    total = sum(weights)
    spans: list[tuple[float, float]] = []
    seen = 0
    for weight in weights:
        span_start = start + (end - start) * seen / total
        seen += weight
        spans.append((span_start, start + (end - start) * seen / total))
    return spans


def _interpolate(times: list[tuple[float, float] | None]) -> list[tuple[float, float]]:
    """Las palabras sin tiempo se reparten en el hueco entre sus vecinas con tiempo."""
    result: list[tuple[float, float]] = []
    index = 0
    while index < len(times):
        timed = times[index]
        if timed is not None:
            result.append(timed)
            index += 1
            continue
        end_of_gap = index
        while end_of_gap < len(times) and times[end_of_gap] is None:
            end_of_gap += 1
        left = result[-1][1] if result else 0.0
        count = end_of_gap - index
        after = times[end_of_gap] if end_of_gap < len(times) else None
        right = after[0] if after is not None else left + TRAILING_WORD_SECONDS * count
        for step in range(count):
            result.append((left + (right - left) * step / count, left + (right - left) * (step + 1) / count))
        index = end_of_gap
    return result


def align(script: str, whisper_words: Sequence[dict]) -> list[dict[str, Any]]:
    """Palabras del guion con los tiempos de whisper (difflib). Cada palabra del guion queda con tiempo.

    Las palabras iguales toman su tiempo; un tramo de whisper que no cuadra en cantidad se reparte entre las palabras
    del guion; las que no tienen par se interpolan entre sus vecinas.
    """
    script_words = script.split()
    script_norm = [_norm(word) for word in script_words]
    whisper_norm = [_norm(w['word']) for w in whisper_words]
    times: list[tuple[float, float] | None] = [None] * len(script_words)
    matcher = difflib.SequenceMatcher(None, script_norm, whisper_norm, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1):
            for offset in range(i2 - i1):
                heard = whisper_words[j1 + offset]
                times[i1 + offset] = (heard['start'], heard['end'])
        elif tag == 'replace':
            spans = _split_by_chars(script_words[i1:i2], whisper_words[j1]['start'], whisper_words[j2 - 1]['end'])
            for offset, span in enumerate(spans):
                times[i1 + offset] = span
    return [
        {'word': word, 'start': start, 'end': end}
        for word, (start, end) in zip(script_words, _interpolate(times), strict=True)
    ]


def _document(
    cues: Sequence[dict],
    *,
    source_path: str,
    kind: str,
    language: str,
    speakers: dict[str, dict] | None = None,
) -> dict[str, Any]:
    built = []
    for number, cue in enumerate(cues, start=1):
        item: dict[str, Any] = {
            'id': number,
            'start': cue['start'],
            'end': cue['end'],
            'text': cue['text'],
            'words': cue['words'],
        }
        if cue.get('speaker') is not None:
            item['speaker'] = cue['speaker']
        built.append(item)
    return new_document(source_path=source_path, kind=kind, language=language, cues=built, speakers=speakers)


def _word(word: dict[str, Any]) -> dict[str, Any]:
    """Una palabra del documento: su tiempo y su texto, y su hablante si la tiene."""
    kept: dict[str, Any] = {'start': word['start'], 'end': word['end'], 'text': word['word']}
    if word.get('speaker') is not None:
        kept['speaker'] = word['speaker']
    return kept


def from_words(
    words: Sequence[dict],
    *,
    source_path: str,
    kind: str,
    language: str,
    speakers: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """Documento con los cues de `segment` a partir de palabras `{word, start, end}`.

    faster-whisper pone un espacio delante de cada palabra (« hola»): se quita para que el cue no tenga dobles espacios.
    """
    words = [{**word, 'word': word['word'].strip()} for word in words]
    cues = [{**cue, 'words': [_word(w) for w in cue['words']]} for cue in segment(words)]
    return _document(cues, source_path=source_path, kind=kind, language=language, speakers=speakers)


def from_cleaner(
    words: Sequence[dict], *, source_path: str, language: str, speakers: dict[str, dict] | None = None
) -> dict[str, Any]:
    """Origen del limpiador: sus palabras ya están en el tiempo del limpio; no hay transcripción nueva."""
    return from_words(words, source_path=source_path, kind='cleaner', language=language, speakers=speakers)


def from_narration(script: str, whisper_words: Sequence[dict], *, source_path: str, language: str) -> dict[str, Any]:
    """Origen de narración: el texto del guion con los tiempos que whisper oyó, y después la segmentación."""
    return from_words(align(script, whisper_words), source_path=source_path, kind='narration', language=language)


def from_import(raw: str, *, source_path: str, language: str) -> dict[str, Any]:
    """Origen importado: un SRT o un VTT, que se reconoce por su cabecera WEBVTT."""
    is_vtt = raw.lstrip('﻿').lstrip().startswith('WEBVTT')
    cues = parse_vtt(raw) if is_vtt else parse_srt(raw)
    return _document(cues, source_path=source_path, kind='import', language=language)
