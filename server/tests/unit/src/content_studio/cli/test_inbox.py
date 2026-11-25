"""Spec 030, fase 2: `studio inbox` desde la terminal (AC-1): agregar, listar y quitar carpetas."""

import json

from content_studio.cli.main import main


def test_ac1_cli_adds_lists_and_removes_a_folder(tmp_path, capsys):
    folder = tmp_path / 'entrada'
    folder.mkdir()
    db = str(tmp_path / 'base.db')

    assert main(['inbox', 'add', str(folder), '--kind', 'media.normalize', '--param', 'preset=custom', '--db', db]) == 0
    added = json.loads(capsys.readouterr().out)
    assert added['path'] == str(folder.resolve())
    assert added['keep_awake'] is True

    assert main(['inbox', 'list', '--db', db]) == 0
    assert [item['id'] for item in json.loads(capsys.readouterr().out)] == [added['id']]

    assert main(['inbox', 'remove', str(added['id']), '--db', db]) == 0
    assert main(['inbox', 'remove', str(added['id']), '--db', db]) == 1


def test_ac1_cli_bad_folder_exits_2_with_the_code(tmp_path, capsys):
    db = str(tmp_path / 'base.db')

    assert main(['inbox', 'add', str(tmp_path / 'no-existe'), '--kind', 'media.normalize', '--db', db]) == 2
    assert 'inbox_path_not_found' in capsys.readouterr().err
