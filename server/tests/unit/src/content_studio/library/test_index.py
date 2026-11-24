"""Índice de la biblioteca (spec 020, D-1 y AC-1): salidas de los trabajos con sus metadatos, sin contenido."""

from __future__ import annotations

import json
import shutil
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

from content_studio.db import connection, jobs, schema
from content_studio.library import index

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def _db(tmp_path: Path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    return conn


def _wav(path: Path, seconds: float = 1.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={seconds}',
         str(path)],
        check=True,
    )  # fmt: skip
    return path


def _done_job(conn, tmp_path: Path, kind: str, name: str, status: str = 'done') -> dict:
    out = tmp_path / 'out' / kind / name
    out.mkdir(parents=True, exist_ok=True)
    job_id = jobs.insert(conn, kind, 'cpu', {'text': name})
    jobs.update(conn, job_id, status=status, output_dir=str(out))
    return jobs.get(conn, job_id)


@pytest.mark.parametrize(
    ('name', 'expected'),
    [('voz.WAV', 'audio'), ('clip.mp4', 'video'), ('charla.srt', 'subtitle'), ('logo.png', 'other'), ('a.json', None)],
)
def test_media_type_by_extension(name, expected):
    """Audio, video y subtítulos por extensión; las imágenes son `other`; lo demás no se indexa."""
    assert index.media_type(Path(name)) == expected


@pytest.mark.parametrize(
    ('kind', 'expected'),
    [('narration', 'narration'), ('narration.regenerate', 'narration'), ('media.convert', 'convert'),
     ('clean.render', 'clean'), ('mix.render', 'mix'), ('engine.install', None), ('editor.proxy', None)],
)  # fmt: skip
def test_kind_of_a_job(kind, expected):
    """El `kind` del ítem sale del trabajo; los de mantenimiento (motores, proxies) no dejan salidas."""
    assert index.item_kind(kind) == expected


@needs_ffmpeg
def test_ac1_a_finished_narration_registers_its_take_with_duration_and_size(tmp_path):
    """AC-1: la toma queda con `origin = job`, su `kind`, la duración y el tamaño; `blocks/` y JSON no entran."""
    with closing(_db(tmp_path)) as conn:
        job = _done_job(conn, tmp_path, 'narration', 'hola')
        take = _wav(Path(job['output_dir']) / 'take.wav', 1.0)
        _wav(Path(job['output_dir']) / 'blocks' / 'b0.wav', 0.5)
        (Path(job['output_dir']) / 'params.json').write_text('{}', encoding='utf-8')

        index.register_job(conn, job)

        [item] = conn.execute('SELECT * FROM library_items').fetchall()
    assert (item['path'], item['origin'], item['job_id'], item['kind']) == (str(take), 'job', job['id'], 'narration')
    assert item['media_type'] == 'audio'
    assert item['size'] == take.stat().st_size
    assert item['duration'] == pytest.approx(1.0, abs=0.05)


def test_register_twice_keeps_one_row_per_path(tmp_path):
    """Volver a registrar el mismo trabajo actualiza la fila (la ruta es única)."""
    with closing(_db(tmp_path)) as conn:
        job = _done_job(conn, tmp_path, 'mix.render', 'mezcla')
        (Path(job['output_dir']) / 'mix.srt').write_text('1\n00:00:00,000 --> 00:00:01,000\nhola\n', encoding='utf-8')

        index.register_job(conn, job)
        index.register_job(conn, job)

        rows = conn.execute('SELECT kind, media_type, duration FROM library_items').fetchall()
    assert [tuple(row) for row in rows] == [('mix', 'subtitle', None)]


def test_ac1_backfill_indexes_the_done_jobs_once(tmp_path):
    """AC-1: tras la migración, los trabajos `done` anteriores entran una sola vez; los fallidos no."""
    with closing(_db(tmp_path)) as conn:
        done = _done_job(conn, tmp_path, 'media.convert', 'uno')
        failed = _done_job(conn, tmp_path, 'media.convert', 'dos', status='error')
        for job in (done, failed):
            (Path(job['output_dir']) / 'clip.srt').write_text('', encoding='utf-8')

        first = index.backfill(conn)
        second = index.backfill(conn)

        paths = [row[0] for row in conn.execute('SELECT path FROM library_items')]
    assert (first, second) == (1, 0)
    assert paths == [str(Path(done['output_dir']) / 'clip.srt')]


def test_a_job_without_output_folder_registers_nothing(tmp_path):
    """Un trabajo sin carpeta (o con una que ya no existe) no deja ítems ni falla."""
    with closing(_db(tmp_path)) as conn:
        job_id = jobs.insert(conn, 'music', 'gpu', {})
        jobs.update(conn, job_id, status='done', output_dir=str(tmp_path / 'gone'))

        assert index.register_job(conn, jobs.get(conn, job_id)) == []


@needs_ffmpeg
def test_an_editor_export_outside_the_job_folder_is_registered_from_its_result(tmp_path):
    """Spec 023: el render del Editor deja el archivo en `exports/` del proyecto y su ruta en `result.json`."""
    conn = _db(tmp_path)
    job = _done_job(conn, tmp_path, 'editor.render', 'render')
    export = _wav(tmp_path / 'proyecto' / 'exports' / 'final.wav')
    (Path(job['output_dir']) / 'result.json').write_text(
        json.dumps({'status': 'done', 'output': str(export)}), encoding='utf-8'
    )

    [item] = index.register_job(conn, job)

    row = conn.execute('SELECT path, kind, job_id FROM library_items WHERE id = ?', (item,)).fetchone()
    assert tuple(row) == (str(export), 'editor', job['id'])


def test_a_result_without_a_media_output_adds_nothing(tmp_path):
    """Un `result.json` sin `output`, roto o que apunta a algo que no es un medio no agrega ítems."""
    conn = _db(tmp_path)
    job = _done_job(conn, tmp_path, 'editor.render', 'render')
    result = Path(job['output_dir']) / 'result.json'
    for text in ('{"status": "done"}', 'roto', json.dumps({'output': str(tmp_path / 'nada.wav')})):
        result.write_text(text, encoding='utf-8')
        assert index.register_job(conn, job) == []
