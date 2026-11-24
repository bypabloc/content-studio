"""Publicar (spec 021, D-4): títulos, descripción, hashtags y capítulos por plataforma a partir de la transcripción.

Los límites de cada plataforma son datos (`llm/platforms.json`). Los capítulos van solo en YouTube: el primero en 0:00,
al menos 3, separados por 10 s o más y cada uno en el inicio de un segmento real. `publish.json` queda en la carpeta del
trabajo y `library_items.publish_path` guarda solo su ruta.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path

from content_studio.db import connection
from content_studio.llm import prompts

PLATFORMS: dict[str, dict] = json.loads(
    Path(__file__).parents[1].joinpath('platforms.json').read_text(encoding='utf-8')
)
MIN_CHAPTERS = 3
CHAPTER_GAP = 10.0
MAX_TRANSCRIPT = 12_000  # caracteres: cabe con el prompt en 8192 tokens
HASHTAG = re.compile(r'#\w+')
Ask = Callable[..., dict]


def prepare(conn: sqlite3.Connection, params: dict) -> tuple[dict, None]:
    """Agrega el archivo del ítem, su duración y su transcripción en caché (la más reciente)."""
    item = conn.execute('SELECT path, duration FROM library_items WHERE id = ?', (params.get('item_id'),)).fetchone()
    if item is None:
        return params, None
    row = conn.execute(
        'SELECT json_path FROM transcripts WHERE source_path = ? ORDER BY id DESC LIMIT 1', (item[0],)
    ).fetchone()
    transcript = row[0] if row and Path(row[0]).is_file() else None
    return {**params, 'source': item[0], 'duration': item[1], 'transcript': transcript}, None


def validate(params: dict) -> list[dict]:
    """El ítem existe, tiene transcripción y las plataformas son conocidas."""
    if not params.get('source'):
        return [{'code': 'item_not_found', 'params': {'item_id': params.get('item_id')}}]
    if not params.get('transcript'):
        return [{'code': 'no_transcript', 'params': {}}]
    platforms = params.get('platforms')
    if not isinstance(platforms, list) or not platforms or not set(platforms) <= PLATFORMS.keys():
        return [{'code': 'unknown_platform', 'params': {'platform': str(platforms)}}]
    return []


def wants_chapters(platform: str, segments: list[dict], duration: float) -> bool:
    """Capítulos solo en la plataforma que los usa y si caben 3 de 10 s."""
    starts = {segment['start'] for segment in segments}
    return bool(PLATFORMS[platform]['chapters']) and duration >= MIN_CHAPTERS * CHAPTER_GAP and len(starts) >= 3


def snap(chapters: list[dict], segments: list[dict]) -> list[dict]:
    """Cada `t` al inicio de segmento más cercano (el anterior si empata), el primero en 0 y sin repetidos."""
    starts = sorted({float(segment['start']) for segment in segments})
    snapped: list[dict] = []
    for chapter in sorted(chapters, key=lambda item: item['t']):
        t = min(starts, key=lambda start: (abs(start - chapter['t']), start))
        t = 0.0 if not snapped else t
        if not snapped or t > snapped[-1]['t']:
            snapped.append({'t': t, 'title': chapter['title'].strip()})
    return snapped


def _schema(platform: str, chapters: bool) -> dict:
    limits = PLATFORMS[platform]
    properties: dict = {
        'titles': {
            'type': 'array',
            'items': {'type': 'string', 'minLength': 1, 'maxLength': limits['title']},
            'minItems': 3,
            'maxItems': 3,
        },
        'description': {'type': 'string', 'minLength': 1, 'maxLength': limits['description']},
        'hashtags': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': limits['hashtags']},
    }
    if chapters:
        chapter = {
            'type': 'object',
            'properties': {'t': {'type': 'number'}, 'title': {'type': 'string', 'maxLength': 100}},
        }
        properties['chapters'] = {'type': 'array', 'items': {**chapter, 'required': ['t', 'title']}}
    return {'type': 'object', 'properties': properties, 'required': ['titles', 'description', 'hashtags']}


def checker(platform: str, segments: list[dict], duration: float) -> Callable[[dict], list[str]]:
    """Lo que el schema no ve: los títulos dentro del límite, hashtags de una palabra y capítulos válidos."""
    limits = PLATFORMS[platform]

    def check(answer: dict) -> list[str]:
        found = [
            f'$.titles: longer than {limits["title"]}' for title in answer['titles'] if len(title) > limits['title']
        ]
        found += [
            f'$.hashtags: {tag!r} must be one word starting with #'
            for tag in answer['hashtags']
            if not HASHTAG.fullmatch(tag)
        ]
        if wants_chapters(platform, segments, duration):
            times = [chapter['t'] for chapter in snap(answer.get('chapters', []), segments)]
            if len(times) < MIN_CHAPTERS or any(b - a < CHAPTER_GAP for a, b in zip(times, times[1:], strict=False)):
                found.append(f'$.chapters: at least {MIN_CHAPTERS}, from 0:00 and {CHAPTER_GAP:.0f} s apart')
        return found

    return check


def _transcript(segments: list[dict]) -> str:
    lines = [f'[{int(s["start"]) // 60}:{int(s["start"]) % 60:02d}] {s["text"].strip()}' for s in segments]
    step = 1
    while len('\n'.join(lines[::step])) > MAX_TRANSCRIPT:
        step += 1
    return '\n'.join(lines[::step])


def run(params: dict, ask: Ask) -> dict:
    """Una propuesta por plataforma: 3 títulos, descripción, hashtags y, en YouTube, capítulos."""
    segments = json.loads(Path(params['transcript']).read_text(encoding='utf-8'))['segments']
    duration = float(params.get('duration') or (segments[-1]['end'] if segments else 0))
    result: dict[str, dict] = {}
    for platform in params['platforms']:
        limits, chapters = PLATFORMS[platform], wants_chapters(platform, segments, duration)
        message = prompts.render(
            'publish',
            platform=limits['label'],
            title=limits['title'],
            description=limits['description'],
            hashtags=limits['hashtags'],
            chapters='Incluye capítulos: el primero en 0:00, al menos 3, separados por 10 s o más.' if chapters else '',
            transcript=_transcript(segments),
        )
        answer = ask(
            [{'role': 'user', 'content': message}],
            _schema(platform, chapters),
            check=checker(platform, segments, duration),
        )
        answer.pop('chapters', None) if not chapters else answer.update(chapters=snap(answer['chapters'], segments))
        result[platform] = answer
    return {'platforms': result}


def finish(params: dict, out_dir: Path, result: dict) -> None:
    """Escribe publish.json y guarda su ruta en el ítem (solo la ruta)."""
    target = out_dir / 'publish.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    database = os.environ.get('CONTENT_STUDIO_DB')
    if database:
        with closing(connection.connect(Path(database))) as conn:
            conn.execute('UPDATE library_items SET publish_path = ? WHERE id = ?', (str(target), params['item_id']))
