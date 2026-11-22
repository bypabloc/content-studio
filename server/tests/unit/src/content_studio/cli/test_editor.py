"""`studio editor render` (spec 017, D-4): un proyecto que no existe sale con 2 antes de encolar."""

from __future__ import annotations

import pytest

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
