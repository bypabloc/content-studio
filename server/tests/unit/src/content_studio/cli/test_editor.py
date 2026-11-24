"""`studio editor render` (spec 017, D-4): un proyecto que no existe sale con 2 antes de encolar."""

from __future__ import annotations

import pytest

from content_studio.cli import editor
from content_studio.cli.main import main


def test_editor_render_refuses_a_project_file_that_does_not_exist(tmp_path, capsys):
    """Un `project.json` que no existe sale con 2 antes de encolar nada, y el mensaje lleva su ruta."""
    missing = tmp_path / 'editor' / 'no-existe' / 'project.json'

    code = main(['editor', 'render', '--project', str(missing), '--db', str(tmp_path / 'base.db')])

    assert code == 2
    assert str(missing.resolve()) in capsys.readouterr().err


def test_editor_render_only_accepts_the_loudness_presets_of_015(tmp_path):
    """Las sonoridades son las de la 015 (podcast, youtube, broadcast); otra cosa la rechaza el parser con exit 2."""
    with pytest.raises(SystemExit) as caught:
        main(
            ['editor', 'render', '--project', 'x/project.json', '--normalize', 'radio', '--db', str(tmp_path / 'b.db')]
        )

    assert caught.value.code == 2


def test_editor_render_enqueues_the_project_and_prints_a_success(monkeypatch, tmp_path, capsys):
    project = tmp_path / 'editor' / 'project.json'
    project.parent.mkdir()
    project.write_text('{}', encoding='utf-8')
    expected = {'status': 'done', 'output_dir': 'exports'}
    calls = []
    monkeypatch.setattr(editor.submit, 'execute', lambda *args: calls.append(args) or expected)
    monkeypatch.setattr(editor, 'main_checkout', lambda root: tmp_path)

    code = main(['editor', 'render', '--project', str(project), '--db', str(tmp_path / 'jobs.db')])

    assert code == 0
    assert calls[0][0:2] == ('editor.render', {'doc': str(project.resolve()), 'format': 'wav'})
    assert calls[0][2] == tmp_path / 'jobs.db'
    assert capsys.readouterr().out == '{"status": "done", "output_dir": "exports"}\n'


def test_editor_render_passes_normalization_and_returns_failure_status(monkeypatch, tmp_path, capsys):
    project = tmp_path / 'project.json'
    project.write_text('{}', encoding='utf-8')
    result = {'status': 'error', 'error': 'codec'}
    calls = []
    monkeypatch.setattr(editor.submit, 'execute', lambda *args: calls.append(args) or result)
    monkeypatch.setattr(editor, 'main_checkout', lambda root: tmp_path)

    code = main(
        [
            'editor',
            'render',
            '--project',
            str(project),
            '--format',
            'mp3',
            '--normalize',
            'podcast',
            '--db',
            str(tmp_path / 'jobs.db'),
        ]
    )

    assert code == 1
    assert calls[0][1] == {'doc': str(project.resolve()), 'format': 'mp3', 'normalize': 'podcast'}
    assert capsys.readouterr().out == '{"status": "error", "error": "codec"}\n'


def test_editor_render_returns_two_when_submit_has_no_result(monkeypatch, tmp_path, capsys):
    project = tmp_path / 'project.json'
    project.write_text('{}', encoding='utf-8')
    monkeypatch.setattr(editor.submit, 'execute', lambda *args: None)
    monkeypatch.setattr(editor, 'main_checkout', lambda root: tmp_path)

    code = main(['editor', 'render', '--project', str(project), '--db', str(tmp_path / 'jobs.db')])

    assert code == 2
    assert capsys.readouterr().out == ''
