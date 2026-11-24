"""Publicar: títulos, descripción, hashtags y capítulos por plataforma, spec 021 AC-8."""

import json
import os
from contextlib import closing

import pytest

from content_studio.db import connection, schema
from content_studio.llm.tasks import publish

# Un video de 5 minutos: un segmento cada 20 s.
SEGMENTS = [{'start': i * 20.0, 'end': i * 20.0 + 18.0, 'text': f'parte {i} del video'} for i in range(15)]


def _setup(tmp_path):
    db = tmp_path / 'base.db'
    transcript = tmp_path / 'words.json'
    transcript.write_text(json.dumps({'segments': SEGMENTS, 'words': []}), encoding='utf-8')
    video = tmp_path / 'demo.mp4'
    video.write_bytes(b'video')
    with closing(connection.connect(db)) as conn:
        schema.migrate(conn)
        conn.execute(
            'INSERT INTO library_items (path, kind, origin, size, mtime, duration, media_type, indexed_at) '
            "VALUES (?, 'watched', 'watched', 5, 0, 300, 'video', '2026-11-24')",
            (str(video),),
        )
        conn.execute(
            'INSERT INTO transcripts (source_path, source_mtime, source_size, model, language, json_path, created_at) '
            "VALUES (?, 0, 5, 'large-v3-turbo', 'es', ?, '2026-11-24')",
            (str(video), str(transcript)),
        )
    return db, video, transcript


def _answer(platform):
    answer = {
        'titles': ['Cómo vender más', 'Tres ideas', 'Guía rápida'],
        'description': 'Un video.',
        'hashtags': ['#ventas'],
    }
    if platform == 'youtube':
        answer['chapters'] = [
            {'at': '0:05', 'title': 'Inicio'},
            {'at': '1:10', 'title': 'Primera idea'},
            {'at': '2:11', 'title': 'Segunda idea'},
            {'at': '3:25', 'title': 'Cierre'},
        ]
    return answer


def test_ac8_prepare_finds_the_item_and_its_cached_transcript(tmp_path):
    """El trabajo recibe la ruta del archivo, su transcripción en caché y la duración."""
    db, video, transcript = _setup(tmp_path)
    with closing(connection.connect(db)) as conn:
        params, _ = publish.prepare(conn, {'item_id': 1, 'platforms': ['youtube']})
        missing, _ = publish.prepare(conn, {'item_id': 99, 'platforms': ['youtube']})

    assert (params['source'], params['transcript'], params['duration']) == (str(video), str(transcript), 300)
    assert publish.validate(params) == []
    assert publish.validate(missing)[0]['code'] == 'item_not_found'
    assert publish.validate({**params, 'platforms': ['myspace']})[0]['code'] == 'unknown_platform'


def test_ac8_youtube_chapters_start_at_zero_snap_to_segments_and_respect_the_limits(tmp_path, monkeypatch):
    """Capítulos: el primero en 0:00, al menos 3, separados ≥ 10 s y cada t en el inicio de un segmento."""
    db, _, transcript = _setup(tmp_path)
    params = {'item_id': 1, 'platforms': ['youtube', 'reels'], 'transcript': str(transcript), 'duration': 300}

    result = publish.run(
        params,
        lambda messages, rule, check=None: _answer('youtube' if 'YouTube' in messages[-1]['content'] else 'reels'),
    )

    youtube = result['platforms']['youtube']
    times = [chapter['t'] for chapter in youtube['chapters']]
    assert times == [0.0, 60.0, 140.0, 200.0]
    starts = {segment['start'] for segment in SEGMENTS}
    assert set(times) <= starts
    assert all(b - a >= 10 for a, b in zip(times, times[1:], strict=False))
    assert all(len(title) <= 100 for title in youtube['titles'])
    assert 'chapters' not in result['platforms']['reels']


def test_ac8_the_check_rejects_titles_over_the_limit_and_bad_hashtags():
    """Un título de más de 100 caracteres o un hashtag con espacios no valida: el cliente reintenta."""
    check = publish.checker('youtube', SEGMENTS, 300)
    assert check(_answer('youtube')) == []
    assert check({**_answer('youtube'), 'titles': ['x' * 101, 'a', 'b']})
    assert check({**_answer('youtube'), 'hashtags': ['#dos palabras']})
    assert check({**_answer('youtube'), 'chapters': [{'at': '0:00', 'title': 'a'}, {'at': '1:40', 'title': 'b'}]})


def test_ac8_finish_writes_publish_json_and_the_base_keeps_only_the_path(tmp_path, monkeypatch):
    """publish.json queda en la carpeta del trabajo y library_items guarda solo su ruta."""
    db, _, _ = _setup(tmp_path)
    monkeypatch.setitem(os.environ, 'CONTENT_STUDIO_DB', str(db))
    out = tmp_path / 'job'
    out.mkdir()

    publish.finish({'item_id': 1}, out, {'platforms': {'youtube': _answer('youtube')}})

    assert json.loads((out / 'publish.json').read_text(encoding='utf-8'))['platforms']['youtube']['titles']
    with closing(connection.connect(db)) as conn:
        row = conn.execute('SELECT publish_path FROM library_items WHERE id = 1').fetchone()
    assert row[0] == str(out / 'publish.json')


def test_a_long_description_is_cut_at_the_last_sentence_that_fits():
    """Reels pide 2200: el modelo se pasaba en los dos intentos y el trabajo fallaba; ahora se corta en una oración."""
    text = 'Primera idea. Segunda idea más larga. Tercera.'

    assert publish.fit(text, 100) == text
    assert publish.fit(text, 30) == 'Primera idea.'
    assert publish.fit('sinpuntosnada' * 5, 20) == ('sinpuntosnada' * 5)[:20]
    assert 'maxLength' not in publish._schema('reels', False)['properties']['description']


def test_chapter_times_come_as_minutes_and_seconds():
    """El modelo escribía 0.51 por 0:51: los tiempos se piden en `m:ss` y se pasan a segundos."""
    chapters = [{'at': '0:00', 'title': 'a'}, {'at': '0:51', 'title': 'b'}, {'at': '1:39', 'title': 'c'}]

    assert [chapter['t'] for chapter in publish.snap(chapters, SEGMENTS)] == [0.0, 60.0, 100.0]
    assert publish._schema('youtube', True)['properties']['chapters']['items']['properties']['at']['pattern']


@pytest.mark.parametrize(('duration', 'expected'), [(300, True), (25, False)])
def test_chapters_are_dropped_when_the_video_is_too_short(duration, expected):
    """En un video corto no caben 3 capítulos de 10 s: se omiten en vez de inventarlos."""
    segments = [{'start': i * 5.0, 'end': i * 5.0 + 4, 'text': 'x'} for i in range(int(duration // 5))]
    assert publish.wants_chapters('youtube', segments, duration) is expected
