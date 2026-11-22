"""Rutas de Mezcla (spec 016, D-3): preparar un proyecto con la transcripción de su voz, sus regiones y su curva."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.db import schema
from content_studio.db.connection import connect
from content_studio.transcription import cache

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
WORDS = [(1.0, 1.4), (1.6, 2.0), (4.0, 4.5)]  # dos tramos de voz tras unir las palabras (ver speech_regions)


def _wav(path: Path, seconds: int) -> Path:
    """Un WAV de `seconds` s con ffmpeg (la voz o la música de prueba)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=440:duration={seconds}',
            str(path),
        ],
        check=True,
    )
    return path


def _cache_transcript(api, voice: Path, words) -> None:
    """Deja en la caché la transcripción de `voice` con sus palabras, como si ya se hubiera transcrito."""
    doc = {
        'duration': 6.0,
        'segments': [{'start': s, 'end': e, 'words': [{'start': s, 'end': e, 'word': 'x'}]} for s, e in words],
    }
    transcript = api.tmp / 'transcripts' / 'voice.json'
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(json.dumps(doc), encoding='utf-8')
    stat = voice.stat()
    conn = connect(api.tmp / 'base.db')
    try:
        cache.store(conn, str(voice), stat.st_mtime, stat.st_size, 'large-v3-turbo', 'auto', str(transcript))
        conn.commit()
    finally:
        conn.close()


@needs_ffmpeg
def test_prepare_with_a_cached_transcript_gives_the_speech_regions_at_once(api):
    """AC-3 (D-3): con la transcripción en caché, el proyecto nace con sus tramos de voz y no encola nada."""
    voice = _wav(api.tmp / 'out' / 'voice.wav', 6)
    music = _wav(api.tmp / 'out' / 'music.wav', 12)
    _cache_transcript(api, voice, WORDS)

    response = api.client.post('/mix/prepare', json={'voice': str(voice), 'music': str(music)}, headers=api.headers)

    assert response.status_code == 201
    body = response.json()
    assert body['regions'] == [[0.8, 2.4], [3.8, 4.9]]
    assert body['transcribe_job'] is None
    assert body['status'] == 'ready'


@needs_ffmpeg
def test_prepare_without_a_transcript_queues_a_transcribe_job(api):
    """Sin caché, el proyecto encola un trabajo `transcribe` de su voz: sus regiones llegan cuando termina."""
    voice = _wav(api.tmp / 'out' / 'voice.wav', 6)
    music = _wav(api.tmp / 'out' / 'music.wav', 12)

    body = api.client.post('/mix/prepare', json={'voice': str(voice), 'music': str(music)}, headers=api.headers).json()

    assert body['regions'] == []
    assert body['status'] == 'transcribing'
    job = api.client.get(f'/jobs/{body["transcribe_job"]}', headers=api.headers).json()
    assert job['kind'] == 'transcribe'


@needs_ffmpeg
def test_put_keeps_the_edited_regions_and_the_curve_follows_them(api):
    """AC-6 (servidor): guardar regiones editadas las deja en `mix.json`, y `/curve` baja la música en ellas."""
    voice = _wav(api.tmp / 'out' / 'voice.wav', 6)
    music = _wav(api.tmp / 'out' / 'music.wav', 12)
    _cache_transcript(api, voice, WORDS)
    project = api.client.post(
        '/mix/prepare', json={'voice': str(voice), 'music': str(music)}, headers=api.headers
    ).json()

    saved = api.client.put(
        f'/mix/{project["id"]}',
        json={'regions': [[1.0, 2.0]], 'params': {'duck_db': -12, 'ramp_ms': 300}},
        headers=api.headers,
    )
    curve = api.client.get(f'/mix/{project["id"]}/curve', headers=api.headers).json()

    assert saved.status_code == 200
    assert saved.json()['regions'] == [[1.0, 2.0]]
    points = dict((round(t, 3), db) for t, db in curve['points'])
    assert points[1.0] == pytest.approx(-12)
    assert points[0.0] == pytest.approx(0)
    assert curve['total'] == pytest.approx(6, abs=0.05)


def test_migration_six_creates_the_mix_projects_table(tmp_path):
    """La migración 6 crea `mix_projects` solo con nombre, ruta y fechas: ningún BLOB, porque la base guarda rutas."""
    conn = connect(tmp_path / 'base.db')
    try:
        schema.migrate(conn)
        columns = {row['name']: row['type'] for row in conn.execute('PRAGMA table_info(mix_projects)')}
        version = conn.execute('PRAGMA user_version').fetchone()[0]
    finally:
        conn.close()

    assert version == 6
    assert set(columns) == {'id', 'name', 'doc_path', 'created_at', 'updated_at'}
    assert 'BLOB' not in columns.values()
