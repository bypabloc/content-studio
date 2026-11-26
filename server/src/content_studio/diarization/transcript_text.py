"""Texto por turnos (spec 036, D-3): «[hh:mm:ss] Nombre: texto», un bloque por cambio de hablante."""

from __future__ import annotations

from typing import Any

from content_studio.diarization import blocks as turn_blocks


def clock(seconds: float) -> str:
    """Segundos como hh:mm:ss, sin decimales.

    >>> clock(3725.9)
    '01:02:05'
    """
    total = int(seconds)
    return f'{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}'


def transcript_text(payload: dict[str, Any], speakers: dict[str, dict[str, str]], timestamps: bool) -> str:
    """Un bloque por turno si hay hablantes; si no, una línea por segmento. Termina en salto de línea."""
    words = [word for segment in payload['segments'] for word in segment.get('words', [])]
    if any(word.get('speaker') for word in words):
        lines = [
            _line(block['start'], _text(block['words']), _name(block['speaker'], speakers), timestamps)
            for block in turn_blocks.blocks(words)
        ]
    else:
        lines = [
            _line(segment['start'], segment.get('text', '').strip(), None, timestamps)
            for segment in payload['segments']
        ]
    return ''.join(f'{line}\n' for line in lines)


def _line(start: float, text: str, name: str | None, timestamps: bool) -> str:
    prefix = f'[{clock(start)}] ' if timestamps else ''
    return f'{prefix}{name}: {text}' if name else f'{prefix}{text}'


def _text(words: list[dict[str, Any]]) -> str:
    return ' '.join(word['word'].strip() for word in words if word['word'].strip())


def _name(speaker: str | None, speakers: dict[str, dict[str, str]]) -> str | None:
    if speaker is None:
        return None
    return speakers.get(speaker, {}).get('name', speaker)
