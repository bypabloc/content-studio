"""Ciclo 1 de la spec 003: el changeset sale del modo de git (D-1)."""

from __future__ import annotations

import subprocess

from devtools.test_runner.changeset import files


def git(root, *args):
    subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)


def test_staged_mode_lists_only_indexed_files(tmp_path):
    git(tmp_path, 'init', '-q')
    (tmp_path / 'a.py').write_text('x = 1\n', encoding='utf-8')
    (tmp_path / 'b.py').write_text('y = 2\n', encoding='utf-8')
    git(tmp_path, 'add', 'a.py')

    assert files('staged', None, root=tmp_path) == [tmp_path / 'a.py']


def test_explicit_list_wins_over_mode(tmp_path):
    assert files('staged', [tmp_path / 'c.py'], root=tmp_path) == [tmp_path / 'c.py']
