"""Acciones de la biblioteca (spec 020, D-4, AC-4 y AC-5): origen, repetir, renombrar, mover y papelera."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.db import connection, jobs, schema, settings
from content_studio.library import actions, index, scan


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Base temporal y una papelera simulada (en CI no se usa la de Windows) que anota lo que recibe."""
    trashed: list[Path] = []

    def fake_trash(path: Path) -> None:
        trashed.append(path)
        path.unlink() if path.is_file() else None

    monkeypatch.setattr(actions, 'send_to_trash', fake_trash)
    monkeypatch.setattr(actions, 'protected_roots', lambda: [tmp_path / 'reference', tmp_path / 'engines'])
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    yield conn, tmp_path, trashed
    conn.close()


def _job_item(conn, folder: Path, name: str = 'take.srt', kind: str = 'narration', group: str | None = None):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text('', encoding='utf-8')
    job_id = jobs.insert(conn, kind, 'gpu', {'text': 'hola'}, group_key=group)
    jobs.update(conn, job_id, status='done', output_dir=str(folder), result=json.dumps({'output': str(path)}))
    [item] = index.register_job(conn, jobs.get(conn, job_id))
    return item, job_id, path


def test_origin_brings_the_job_its_other_outputs_and_the_takes_of_its_group(env):
    """D-4: el detalle trae el trabajo (params y fechas), las otras salidas y las tomas del mismo `group_key`."""
    conn, tmp, _ = env
    item, job_id, _ = _job_item(conn, tmp / 'out' / 'a', group='g')
    (tmp / 'out' / 'a' / 'take.vtt').write_text('', encoding='utf-8')
    index.register_job(conn, jobs.get(conn, job_id))
    take, _, _ = _job_item(conn, tmp / 'out' / 'b', group='g')

    detail = actions.origin(conn, item)

    assert detail['job']['params'] == {'text': 'hola'}
    assert [Path(o['path']).name for o in detail['outputs']] == ['take.vtt']
    assert [t['id'] for t in detail['takes']] == [take]


def test_repeat_queues_a_new_job_with_the_same_params(env):
    """«Repetir» encola un trabajo nuevo con los mismos `params` (como `retry`)."""
    conn, tmp, _ = env
    item, job_id, _ = _job_item(conn, tmp / 'out' / 'a')

    new_id = actions.repeat(conn, item)

    assert new_id != job_id
    assert jobs.get(conn, new_id)['params'] == {'text': 'hola'}


def test_ac4_rename_onto_an_existing_file_touches_nothing(env):
    """AC-4: si el destino existe, `FileExistsError` y ni el disco ni la base cambian."""
    conn, tmp, _ = env
    item, _, path = _job_item(conn, tmp / 'out' / 'a')
    (path.parent / 'otro.srt').write_text('x', encoding='utf-8')

    with pytest.raises(FileExistsError):
        actions.rename(conn, item, 'otro.srt')

    assert path.is_file()
    assert conn.execute('SELECT path FROM library_items WHERE id = ?', (item,)).fetchone()[0] == str(path)


def test_ac4_rename_updates_the_disk_the_index_and_the_job_result(env):
    """AC-4: el archivo cambia en disco y la ruta nueva queda en `library_items` y en `jobs.result`."""
    conn, tmp, _ = env
    item, job_id, path = _job_item(conn, tmp / 'out' / 'a')

    renamed = actions.rename(conn, item, 'final')

    target = path.parent / 'final.srt'
    assert (renamed['path'], target.is_file(), path.exists()) == (str(target), True, False)
    assert json.loads(jobs.get(conn, job_id)['result'])['output'] == str(target)


@pytest.mark.parametrize('name', ['', '  ', '../fuera.srt', 'a/b.srt', 'a\\b.srt'])
def test_rename_rejects_empty_names_and_paths(env, name):
    """El nombre nuevo es solo un nombre: ni vacío ni con separadores de carpeta."""
    conn, tmp, _ = env
    item, _, _ = _job_item(conn, tmp / 'out' / 'a')

    with pytest.raises(ValueError):
        actions.rename(conn, item, name)


def test_move_takes_the_file_to_another_folder_and_refuses_to_overwrite(env):
    """Mover cambia de carpeta con el mismo nombre; si ahí ya hay uno, `FileExistsError`."""
    conn, tmp, _ = env
    item, _, path = _job_item(conn, tmp / 'out' / 'a')
    other, _, _ = _job_item(conn, tmp / 'out' / 'b', name='dos.srt')
    (tmp / 'dest').mkdir()
    (tmp / 'dest' / 'dos.srt').write_text('', encoding='utf-8')

    moved = actions.move(conn, item, tmp / 'dest')

    assert (Path(moved['path']), path.exists()) == (tmp / 'dest' / 'take.srt', False)
    with pytest.raises(FileExistsError):
        actions.move(conn, other, tmp / 'dest')
    with pytest.raises(ValueError):
        actions.move(conn, other, tmp / 'no-existe')


def test_ac5_delete_with_files_sends_to_the_trash_and_drops_the_record(env):
    """AC-5: con `files`, el archivo va a la papelera y el registro desaparece; sin `files`, solo el registro."""
    conn, tmp, trashed = env
    item, _, path = _job_item(conn, tmp / 'out' / 'a')
    kept, _, kept_path = _job_item(conn, tmp / 'out' / 'b')

    actions.delete(conn, item, files=True)
    actions.delete(conn, kept, files=False)

    assert trashed == [path]
    assert kept_path.is_file()
    assert conn.execute('SELECT COUNT(*) FROM library_items').fetchone()[0] == 0


def test_delete_the_whole_job_trashes_its_folder_and_all_its_items(env):
    """«Borrar el trabajo completo»: la carpeta del trabajo va a la papelera con todos sus ítems."""
    conn, tmp, trashed = env
    item, job_id, path = _job_item(conn, tmp / 'out' / 'a')
    (path.parent / 'take.vtt').write_text('', encoding='utf-8')
    index.register_job(conn, jobs.get(conn, job_id))

    actions.delete(conn, item, files=True, whole_job=True)

    assert trashed == [path.parent]
    assert conn.execute('SELECT COUNT(*) FROM library_items').fetchone()[0] == 0


def test_ac5_a_path_inside_the_references_is_protected(env):
    """AC-5: una ruta de `reference/` (o de los motores) no se borra, renombra ni mueve: `ProtectedPath`."""
    conn, tmp, trashed = env
    voice = tmp / 'reference' / 'default' / 'neutral.srt'
    voice.parent.mkdir(parents=True)
    voice.write_text('', encoding='utf-8')
    scan.add_folder(conn, tmp / 'reference')
    scan.scan(conn)
    item = conn.execute('SELECT id FROM library_items').fetchone()[0]

    for action in (lambda: actions.delete(conn, item, files=True), lambda: actions.rename(conn, item, 'x')):
        with pytest.raises(actions.ProtectedPath):
            action()

    assert (trashed, voice.is_file()) == ([], True)


def test_forgetting_a_watched_file_can_ignore_it_in_later_scans(env):
    """Sin `files` y con `ignore`, la ruta queda en `library.ignored` y el próximo escaneo no la agrega."""
    conn, tmp, _ = env
    (tmp / 'videos').mkdir()
    (tmp / 'videos' / 'a.srt').write_text('', encoding='utf-8')
    scan.add_folder(conn, tmp / 'videos')
    scan.scan(conn)
    item = conn.execute('SELECT id FROM library_items').fetchone()[0]

    actions.delete(conn, item, files=False, ignore=True)
    scan.scan(conn)

    assert settings.get(conn, scan.IGNORED) == [str(tmp / 'videos' / 'a.srt')]
    assert conn.execute('SELECT COUNT(*) FROM library_items').fetchone()[0] == 0


@pytest.mark.local
def test_ac5_the_real_recycle_bin_receives_a_file_of_the_spec(tmp_path):
    """AC-5 (-m local): `send2trash` real sobre un archivo creado en `tmp/spec-020/`; se puede restaurar a mano."""
    from content_studio import paths

    folder = paths.ROOT / 'tmp' / 'spec-020'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'papelera-{tmp_path.name}.txt'
    target.write_text('prueba de la spec 020', encoding='utf-8')

    actions.send_to_trash(target)

    assert not target.exists()


def test_actions_on_an_unknown_item_or_without_job_fail_clearly(env):
    """Un ítem que no existe da LookupError; repetir un archivo vigilado (sin trabajo), ValueError."""
    conn, tmp, _ = env
    (tmp / 'videos').mkdir()
    (tmp / 'videos' / 'a.srt').write_text('', encoding='utf-8')
    scan.add_folder(conn, tmp / 'videos')
    scan.scan(conn)
    watched = conn.execute('SELECT id FROM library_items').fetchone()[0]

    with pytest.raises(LookupError):
        actions.origin(conn, 999)
    with pytest.raises(ValueError):
        actions.repeat(conn, watched)
    assert actions.origin(conn, watched)['job'] is None
