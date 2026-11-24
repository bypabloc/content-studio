"""Etapa spelling del test-runner: cspell sobre los archivos del changeset (spec 003, D-1)."""

from __future__ import annotations

from devtools.test_runner.spelling import run


def test_no_files_passes_without_running_cspell():
    assert run([]) == {'stage': 'spelling', 'status': 'pass', 'detail': ''}


def test_unknown_word_fails_the_stage(tmp_path):
    note = tmp_path / 'note.py'
    note.write_text('"""Nota."""\n\nqzxvbwkrt = 1\n', encoding='utf-8')

    result = run([note])

    assert result['status'] == 'fail'
    assert 'qzxvbwkrt' in result['detail']
