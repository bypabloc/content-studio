"""Espacio de la biblioteca (spec 020, D-5 y AC-6): sumas por tipo, lo más pesado y las tomas no elegidas."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

import pytest

from content_studio.db import connection, jobs, schema
from content_studio.db.connection import utc_now
from content_studio.library import scan, storage


@pytest.fixture
def conn(tmp_path):
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        yield conn


def _item(conn, path: str, kind: str, size: int, job_id: int | None = None, missing: int = 0) -> int:
    return conn.execute(
        'INSERT INTO library_items (path, kind, origin, job_id, size, mtime, media_type, missing, indexed_at) '
        "VALUES (?, ?, ?, ?, ?, 1, 'audio', ?, ?)",
        (path, kind, 'job' if job_id else 'watched', job_id, size, missing, utc_now()),
    ).lastrowid


def _take(conn, group: str, starred: bool) -> int:
    job_id = jobs.insert(conn, 'narration', 'gpu', {}, group_key=group)
    jobs.update(conn, job_id, status='done')
    if starred:
        jobs.star(conn, job_id)
    return job_id


def test_ac6_sums_by_kind_match_the_sizes_and_skip_missing_files(conn, tmp_path):
    """AC-6: la suma por tipo coincide con los `size`; un faltante no ocupa espacio."""
    _item(conn, '/a/1.wav', 'narration', 100)
    _item(conn, '/a/2.wav', 'narration', 50)
    _item(conn, '/a/3.wav', 'music', 7)
    _item(conn, '/a/4.wav', 'music', 1000, missing=1)

    summary = storage.summary(conn, outputs=tmp_path / 'out')

    assert summary['by_kind'] == [
        {'kind': 'narration', 'size': 150, 'count': 2},
        {'kind': 'music', 'size': 7, 'count': 1},
    ]
    assert [item['size'] for item in summary['heaviest']] == [100, 50, 7]


def test_ac6_unchosen_takes_are_the_non_starred_of_groups_with_a_star(conn, tmp_path):
    """AC-6: solo las tomas no ★ de los grupos que tienen ★; un grupo sin ★ no aparece."""
    chosen, other = _take(conn, 'g1', True), _take(conn, 'g1', False)
    loose = _take(conn, 'g2', False)
    _item(conn, '/a/chosen.wav', 'narration', 1, job_id=chosen)
    unchosen = _item(conn, '/a/other.wav', 'narration', 2, job_id=other)
    _item(conn, '/a/loose.wav', 'narration', 3, job_id=loose)

    summary = storage.summary(conn, outputs=tmp_path / 'out')

    assert [item['id'] for item in summary['unchosen']] == [unchosen]


def test_totals_measure_the_outputs_folder_and_each_watched_folder_on_disk(conn, tmp_path):
    """El total de `outputs_dir()` y de cada carpeta vigilada se mide en disco, también lo no indexado."""
    (tmp_path / 'out' / 'x').mkdir(parents=True)
    (tmp_path / 'out' / 'x' / 'a.bin').write_bytes(b'1234')
    (tmp_path / 'videos').mkdir()
    (tmp_path / 'videos' / 'v.srt').write_bytes(b'12')
    scan.add_folder(conn, tmp_path / 'videos')

    summary = storage.summary(conn, outputs=tmp_path / 'out')

    assert summary['outputs'] == {'path': str(tmp_path / 'out'), 'size': 4}
    assert [(Path(f['path']).name, f['size']) for f in summary['folders']] == [('videos', 2)]
