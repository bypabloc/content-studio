"""Búsqueda y filtros (spec 020, D-2 y AC-9): SQL sobre el índice, con etiquetas, proyectos, ★ y paginado."""

from __future__ import annotations

import time
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pytest

from content_studio.db import connection, jobs, schema
from content_studio.db.connection import utc_now
from content_studio.library import query


def _db(tmp_path: Path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    return conn


def _item(conn, path: str, kind='music', media='audio', size=10, mtime=1.0, duration=None, job_id=None) -> int:
    origin = 'job' if job_id else 'watched'
    return conn.execute(
        'INSERT INTO library_items (path, kind, origin, job_id, size, mtime, duration, media_type, indexed_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (path, kind, origin, job_id, size, mtime, duration, media, utc_now()),
    ).lastrowid


def _names(result: dict) -> list[str]:
    return [item['name'] for item in result['items']]


@pytest.fixture
def conn(tmp_path):
    with closing(_db(tmp_path)) as conn:
        yield conn


def test_text_matches_the_file_name_and_the_tags_not_the_folder(conn):
    """`q` busca en el nombre y en las etiquetas; el nombre de la carpeta del trabajo no cuenta."""
    first = _item(conn, '/out/narration/2026-01-01-1-registrado/take.wav')
    _item(conn, '/out/music/registro-final.wav')
    conn.execute("INSERT INTO tags (name) VALUES ('Reel 12')")
    conn.execute('INSERT INTO item_tags VALUES (?, 1)', (first,))

    assert _names(query.search(conn, q='REGISTR')) == ['registro-final.wav']
    assert _names(query.search(conn, q='reel')) == ['take.wav']


def test_content_search_adds_the_ids_found_on_disk(conn, monkeypatch):
    """Con «Buscar también en el contenido» se suman los ids de `text_search`."""
    found = _item(conn, '/out/narration/take.wav')
    _item(conn, '/out/music/otra.wav')
    monkeypatch.setattr(query.text_search, 'matching_ids', lambda conn, q: {found})

    assert _names(query.search(conn, q='acta', content=True)) == ['take.wav']
    assert _names(query.search(conn, q='acta')) == []


def test_filters_by_kind_media_duration_date_star_tag_project_and_folder(conn, tmp_path):
    """Cada filtro reduce el resultado; se combinan con AND."""
    job_id = jobs.insert(conn, 'narration', 'gpu', {}, group_key='g')
    jobs.star(conn, job_id)
    day = datetime(2026, 3, 10, 12).timestamp()
    starred = _item(conn, '/a/voz.wav', kind='narration', duration=30, mtime=day, job_id=job_id)
    _item(conn, '/a/clip.mp4', kind='convert', media='video', duration=5, mtime=day + 86400 * 5)
    conn.execute("INSERT INTO tags (name) VALUES ('reel')")
    conn.execute('INSERT INTO item_tags VALUES (?, 1)', (starred,))
    conn.execute("INSERT INTO projects (name, created_at) VALUES ('Curso', 'x')")
    conn.execute('INSERT INTO project_items VALUES (1, ?)', (starred,))

    assert _names(query.search(conn, kind='convert')) == ['clip.mp4']
    assert _names(query.search(conn, media_type='audio')) == ['voz.wav']
    assert _names(query.search(conn, min_dur=10)) == ['voz.wav']
    assert _names(query.search(conn, max_dur=10)) == ['clip.mp4']
    assert _names(query.search(conn, date_from='2026-03-12')) == ['clip.mp4']
    assert _names(query.search(conn, date_to='2026-03-11')) == ['voz.wav']
    assert _names(query.search(conn, starred=True)) == ['voz.wav']
    assert _names(query.search(conn, tag='reel')) == ['voz.wav']
    assert _names(query.search(conn, project=1)) == ['voz.wav']
    assert _names(query.search(conn, origin='job')) == ['voz.wav']


def test_items_carry_tags_and_star_and_sort_and_page(conn):
    """Cada ítem trae su nombre, etiquetas y ★; se ordena por fecha, nombre, tamaño o duración y se pagina."""
    for number in range(5):
        _item(conn, f'/a/{number}.wav', size=number, mtime=float(number), duration=float(5 - number))

    newest = query.search(conn, page_size=2)
    by_name = query.search(conn, sort='name', page=2, page_size=2)
    by_size = query.search(conn, sort='size')
    by_duration = query.search(conn, sort='duration')

    assert (newest['total'], _names(newest)) == (5, ['4.wav', '3.wav'])
    assert _names(by_name) == ['2.wav', '3.wav']
    assert _names(by_size)[0] == '4.wav'
    assert _names(by_duration)[0] == '0.wav'
    assert newest['items'][0]['tags'] == [] and newest['items'][0]['starred'] is False


def test_an_unknown_sort_is_rejected(conn):
    """El orden es uno de los de `SORTS`."""
    with pytest.raises(ValueError):
        query.search(conn, sort='random')


def test_ac9_a_name_search_over_5000_items_answers_in_under_300_ms(conn):
    """AC-9: con 5.000 ítems, buscar por nombre tarda menos de 300 ms."""
    conn.execute('BEGIN')
    for number in range(5000):
        _item(conn, f'/out/music/pista-{number:04d}.wav', mtime=float(number))
    conn.execute('COMMIT')

    start = time.perf_counter()
    result = query.search(conn, q='pista-4999')
    elapsed = time.perf_counter() - start

    assert _names(result) == ['pista-4999.wav']
    assert elapsed < 0.3
