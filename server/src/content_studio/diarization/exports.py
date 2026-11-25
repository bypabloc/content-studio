"""Exportaciones de los turnos: RTTM, CSV y JSON (spec 035, AC-3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_studio.diarization import speakers


def rttm(turns: list[dict[str, Any]], uri: str) -> str:
    """Una línea RTTM por turno exclusivo: inicio y duración con 3 decimales."""
    lines = [
        f'SPEAKER {uri} 1 {turn["start"]:.3f} {turn["end"] - turn["start"]:.3f} <NA> <NA> {turn["speaker"]} <NA> <NA>'
        for turn in turns
    ]
    return '\n'.join(lines) + ('\n' if lines else '')


def csv_text(turns: list[dict[str, Any]], speakers: dict[str, dict[str, str]]) -> str:
    """CSV con cabecera start,end,speaker,name; el nombre sale de `speakers`."""
    lines = ['start,end,speaker,name']
    for turn in turns:
        name = speakers.get(turn['speaker'], {}).get('name', turn['speaker'])
        lines.append(f'{turn["start"]:.3f},{turn["end"]:.3f},{turn["speaker"]},{name}')
    return '\n'.join(lines) + '\n'


def write_result(folder: Path | str, result: dict[str, Any]) -> None:
    """Escribe los archivos de una diarización: turns.json, RTTM, CSV, speakers.json y embeddings.json."""
    target = Path(folder)
    names = speakers.build(result['speakers'])
    turns = {key: result[key] for key in ('duration', 'speakers', 'diarization', 'exclusive_diarization')}
    write_all(target, turns, names)
    (target / 'speakers.json').write_text(json.dumps(names, ensure_ascii=False), encoding='utf-8')
    (target / 'embeddings.json').write_text(json.dumps(result.get('embeddings', {})), encoding='utf-8')


def write_all(
    folder: Path | str, result: dict[str, Any], speakers: dict[str, dict[str, str]], uri: str = 'audio'
) -> None:
    """Escribe turns.json (el resultado completo), turns.rttm y turns.csv en `folder`."""
    target = Path(folder)
    target.mkdir(parents=True, exist_ok=True)
    (target / 'turns.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    turns = result['exclusive_diarization']
    (target / 'turns.rttm').write_text(rttm(turns, uri), encoding='utf-8')
    (target / 'turns.csv').write_text(csv_text(turns, speakers), encoding='utf-8')
