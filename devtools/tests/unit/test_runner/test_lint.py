"""Etapa lint del test-runner: ruff check y format --check sobre los .py del changeset."""

from __future__ import annotations

from devtools.test_runner.lint import run


def test_clean_python_file_passes(tmp_path):
    clean = tmp_path / 'clean.py'
    clean.write_text('x = 1\n', encoding='utf-8')

    assert run([clean])['status'] == 'pass'


def test_unused_import_fails_with_the_ruff_code(tmp_path):
    broken = tmp_path / 'broken.py'
    broken.write_text('import os\n', encoding='utf-8')

    result = run([broken])

    assert result['status'] == 'fail'
    assert 'F401' in result['detail']


def test_no_python_files_passes_without_running_ruff(tmp_path):
    notes = tmp_path / 'notes.md'
    notes.write_text('# nada\n', encoding='utf-8')

    assert run([notes]) == {'stage': 'lint', 'status': 'pass', 'detail': ''}
