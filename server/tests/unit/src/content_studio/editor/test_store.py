"""Almacén de proyectos del editor (spec 017, D-1 y D-3): carpetas, hash y escritura que no pisa un cambio (AC-2)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from content_studio.editor import store


def test_slug_is_kebab_case_ascii_and_never_empty():
    """El nombre pasa a kebab-case ASCII; sin letras, el nombre es «proyecto»."""
    assert store.slug('Charla de prueba: ñandú!') == 'charla-de-prueba-nandu'
    assert store.slug('!!!') == 'project'


def test_create_makes_the_dated_folder_with_media_exports_and_the_document(tmp_path):
    """La carpeta es `<AAAA-MM-DD>-<slug>/` y trae `media/`, `exports/` y el documento v2."""
    file = store.create(tmp_path, 'Charla', date(2026, 11, 22))

    assert file.parent.name == '2026-11-22-charla'
    assert (file.parent / 'media').is_dir() and (file.parent / 'exports').is_dir()
    assert json.loads(file.read_text(encoding='utf-8'))['version'] == 2


def test_read_migrates_a_v1_project_and_keeps_the_original_hash(tmp_path):
    """Al leer, la v1 se entrega como v2 y el hash sigue describiendo el archivo original."""
    file = store.create(tmp_path, 'Charla', date(2026, 11, 22))
    old = json.loads(file.read_text(encoding='utf-8'))
    old['version'] = 1
    old.pop('canvas')
    old.pop('transitions')
    original = json.dumps(old).encode('utf-8')
    file.write_bytes(original)

    doc, digest = store.read(file)

    assert doc['version'] == 2
    assert doc['canvas'] == {'width': 1920, 'height': 1080, 'fps': 30, 'background': '#000000'}
    assert doc['transitions'] == []
    assert digest == store.hash_of(original)


def test_a_second_project_with_the_same_name_the_same_day_gets_a_new_folder(tmp_path):
    """Dos proyectos con el mismo nombre el mismo día no se pisan: el segundo lleva `-2`."""
    first = store.create(tmp_path, 'Charla', date(2026, 11, 22))
    second = store.create(tmp_path, 'Charla', date(2026, 11, 22))

    assert second.parent.name == '2026-11-22-charla-2'
    assert first.exists() and second.exists()


def test_write_with_the_current_hash_saves_and_returns_the_new_hash(tmp_path):
    """Con el hash del archivo, la escritura entra y devuelve el hash del contenido nuevo."""
    file = store.create(tmp_path, 'Charla', date(2026, 11, 22))
    doc, digest = store.read(file)

    new_digest = store.write(file, {**doc, 'name': 'Editada'}, digest)

    assert store.read(file) == ({**doc, 'name': 'Editada'}, new_digest)


def test_write_with_a_stale_hash_raises_and_leaves_the_file_and_no_temporary(tmp_path):
    """AC-2: con un hash viejo, `write` lanza `ProjectChanged`, no cambia el archivo y no deja un temporal."""
    file = store.create(tmp_path, 'Charla', date(2026, 11, 22))
    doc, digest = store.read(file)
    store.write(file, {**doc, 'name': 'uno'}, digest)
    before = file.read_bytes()

    with pytest.raises(store.ProjectChanged) as caught:
        store.write(file, {**doc, 'name': 'dos'}, digest)

    assert caught.value.current != digest
    assert file.read_bytes() == before
    assert not (file.parent / 'project.json.tmp').exists()


def test_missing_lists_the_sources_that_do_not_exist_once_each(tmp_path):
    """AC-10: las fuentes relativas se buscan en la carpeta del proyecto; las que no existen salen una sola vez."""
    folder = tmp_path / 'proyecto'
    (folder / 'media').mkdir(parents=True)
    (folder / 'media' / 'existe.wav').write_bytes(b'')
    doc = {
        'clips': [
            {'src': 'media/existe.wav'},
            {'src': 'media/no.wav'},
            {'src': 'media/no.wav'},
            {'src': str(tmp_path / 'absoluta-no.wav')},
        ]
    }

    assert store.missing(folder, doc) == ['media/no.wav', str(tmp_path / 'absoluta-no.wav')]
