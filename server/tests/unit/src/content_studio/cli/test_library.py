"""`studio library` (spec 020): listar, escanear, etiquetar y mandar a la papelera, sin preguntar nada."""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from content_studio.cli.main import main
from content_studio.db import connection
from content_studio.library import actions


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(actions, 'protected_roots', lambda: [tmp_path / 'reference'])
    monkeypatch.setattr(actions, 'send_to_trash', lambda path: path.unlink())
    folder = tmp_path / 'videos'
    folder.mkdir()
    (folder / 'a.srt').write_text('', encoding='utf-8')
    return tmp_path / 'base.db'


def test_scan_list_tag_and_trash(db, tmp_path, capsys):
    """`scan --add` vigila y escanea; `list` muestra el ítem; `tag` lo etiqueta y `trash` lo manda a la papelera."""
    assert main(['library', 'scan', '--add', str(tmp_path / 'videos'), '--db', str(db)]) == 0
    assert json.loads(capsys.readouterr().out) == {'added': 1, 'updated': 0, 'missing': 0}

    assert main(['library', 'list', '--kind', 'watched', '--db', str(db)]) == 0
    [item] = json.loads(capsys.readouterr().out)
    assert main(['library', 'tag', str(item['id']), 'reel', '--db', str(db)]) == 0
    assert json.loads(capsys.readouterr().out) == ['reel']

    assert main(['library', 'trash', item['path'], '--db', str(db)]) == 0
    assert not (tmp_path / 'videos' / 'a.srt').exists()
    with closing(connection.connect(db)) as conn:
        assert conn.execute('SELECT COUNT(*) FROM library_items').fetchone()[0] == 0


def test_trash_inside_the_references_exits_1_with_protected_path(db, tmp_path, capsys):
    """03 §1.3: una ruta de `reference/` sale con 1 y `protected_path`, y el archivo queda."""
    voice = tmp_path / 'reference' / 'default' / 'neutral.wav'
    voice.parent.mkdir(parents=True)
    voice.write_bytes(b'RIFF')

    assert main(['library', 'trash', str(voice), '--db', str(db)]) == 1

    assert json.loads(capsys.readouterr().out) == {'code': 'protected_path'}
    assert voice.is_file()


def test_unknown_items_and_bad_folders_fail(db, tmp_path, capsys):
    """Un ítem que no existe sale con 1; una carpeta que no existe, con 2."""
    assert main(['library', 'tag', '99', 'x', '--db', str(db)]) == 1
    assert main(['library', 'trash', '99', '--db', str(db)]) == 1
    assert main(['library', 'trash', str(tmp_path / 'nada.wav'), '--db', str(db)]) == 1
    assert main(['library', 'scan', '--add', str(tmp_path / 'nada'), '--db', str(db)]) == 2
