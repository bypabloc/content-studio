"""Carpetas vigiladas (spec 020, D-1 y AC-2): se escanean al pedirlo, se marcan los faltantes y nunca se borra nada."""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

import pytest

from content_studio.db import connection, jobs, schema, settings
from content_studio.library import index, scan


def _db(tmp_path: Path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    return conn


def _media(folder: Path, *names: str) -> list[Path]:
    """Subtítulos vacíos: son medios para el índice y no necesitan ffmpeg."""
    created = []
    for name in names:
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('', encoding='utf-8')
        created.append(path)
    return created


def _rows(conn) -> dict[str, int]:
    return {Path(row['path']).name: row['missing'] for row in conn.execute('SELECT path, missing FROM library_items')}


def test_ac2_a_second_scan_marks_the_removed_file_missing_and_never_deletes_rows(tmp_path):
    """AC-2: 3 medios, se agrega uno y se borra otro: 4 ítems, uno con `missing = 1`."""
    folder = tmp_path / 'videos'
    first, *_ = _media(folder, 'a.srt', 'b.srt', 'sub/c.srt')
    with closing(_db(tmp_path)) as conn:
        folder_id = scan.add_folder(conn, folder)
        assert scan.scan(conn) == {'added': 3, 'updated': 0, 'missing': 0}
        _media(folder, 'd.srt')
        first.unlink()

        assert scan.scan(conn, folder_id) == {'added': 1, 'updated': 0, 'missing': 1}

        assert _rows(conn) == {'a.srt': 1, 'b.srt': 0, 'c.srt': 0, 'd.srt': 0}


def test_a_file_that_comes_back_is_no_longer_missing_and_a_change_updates_it(tmp_path):
    """Si el archivo reaparece, deja de faltar; si cambia de tamaño, se actualiza."""
    folder = tmp_path / 'videos'
    [path] = _media(folder, 'a.srt')
    with closing(_db(tmp_path)) as conn:
        scan.add_folder(conn, folder)
        scan.scan(conn)
        path.unlink()
        scan.scan(conn)
        path.write_text('1', encoding='utf-8')

        assert scan.scan(conn) == {'added': 0, 'updated': 1, 'missing': 0}
        assert conn.execute('SELECT size, missing FROM library_items').fetchone()[:] == (1, 0)


def test_ignored_files_and_non_media_are_skipped(tmp_path):
    """`library.ignored` (borrar solo el registro y «ignorar») y lo que no es un medio no entran."""
    folder = tmp_path / 'videos'
    ignored, _ = _media(folder, 'a.srt', 'b.srt')
    (folder / 'notas.txt').write_text('x', encoding='utf-8')
    with closing(_db(tmp_path)) as conn:
        settings.set_value(conn, scan.IGNORED, [str(ignored)])
        scan.add_folder(conn, folder)

        scan.scan(conn)

        assert set(_rows(conn)) == {'b.srt'}


def test_a_job_output_inside_a_watched_folder_keeps_its_origin(tmp_path):
    """Una salida ya indexada por su trabajo no pasa a `watched` al escanear la carpeta que la contiene."""
    folder = tmp_path / 'out'
    [path] = _media(folder / 'convert' / 'job', 'clip.srt')
    with closing(_db(tmp_path)) as conn:
        job_id = jobs.insert(conn, 'media.convert', 'cpu', {})
        jobs.update(conn, job_id, status='done', output_dir=str(path.parent))
        index.register_job(conn, jobs.get(conn, job_id))
        scan.add_folder(conn, folder)

        assert scan.scan(conn)['added'] == 0
        assert conn.execute('SELECT origin, job_id FROM library_items').fetchone()[:] == ('job', job_id)


def test_folders_are_added_once_listed_and_removed_with_their_items(tmp_path):
    """Agregar dos veces la misma carpeta da el mismo id; quitarla borra sus ítems del índice, no los archivos."""
    folder = tmp_path / 'videos'
    [path] = _media(folder, 'a.srt')
    with closing(_db(tmp_path)) as conn:
        folder_id = scan.add_folder(conn, folder, name='Videos')
        assert scan.add_folder(conn, folder) == folder_id
        scan.scan(conn)
        assert [(f['id'], f['name']) for f in scan.list_folders(conn)] == [(folder_id, 'Videos')]

        assert scan.remove_folder(conn, folder_id) is True

        assert scan.list_folders(conn) == []
        assert _rows(conn) == {}
    assert path.is_file()


def test_add_folder_rejects_a_path_that_is_not_a_folder(tmp_path):
    """Una ruta que no es carpeta no se agrega."""
    with closing(_db(tmp_path)) as conn, pytest.raises(ValueError):
        scan.add_folder(conn, tmp_path / 'no-existe')


def test_main_scans_the_database_of_the_job_and_prints_the_counts(tmp_path, monkeypatch, capsys):
    """El trabajo `library.scan` corre `python -m content_studio.library.scan` sobre la base del worker."""
    _media(tmp_path / 'videos', 'a.srt')
    with closing(_db(tmp_path)) as conn:
        scan.add_folder(conn, tmp_path / 'videos')
    monkeypatch.setenv('CONTENT_STUDIO_DB', str(tmp_path / 'base.db'))

    assert scan.main([]) == 0

    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1]) == {'added': 1, 'updated': 0, 'missing': 0}
    with closing(_db(tmp_path)) as conn:
        assert settings.get(conn, scan.LAST_SCAN)
