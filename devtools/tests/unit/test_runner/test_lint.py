"""Etapa lint del test-runner: ruff check y format --check sobre los .py del changeset."""

from __future__ import annotations

import types

from devtools import paths
from devtools.test_runner import lint
from devtools.test_runner.lint import run


def test_files_inside_the_checkout_reach_ruff_as_relative_posix_paths(monkeypatch):
    seen = []
    monkeypatch.setattr(
        lint.subprocess,
        'run',
        lambda cmd, **kwargs: seen.append(cmd) or types.SimpleNamespace(returncode=0, stdout='', stderr=''),
    )

    run([paths.ROOT / 'devtools' / 'paths.py'])

    file_args = [arg for cmd in seen for arg in cmd if arg.endswith('paths.py')]
    assert file_args == ['devtools/paths.py', 'devtools/paths.py']  # ruff check y format --check


def test_clean_python_file_passes(tmp_path):
    clean = tmp_path / 'clean.py'
    clean.write_text('"""Módulo de prueba."""\n\nx = 1\n', encoding='utf-8')

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


def test_ac5_public_function_without_docstring_fails_with_d103(tmp_path):
    undocumented = tmp_path / 'undocumented.py'
    undocumented.write_text('def public() -> int:\n    return 1\n', encoding='utf-8')

    result = run([undocumented])

    assert result['status'] == 'fail'
    assert 'D103' in result['detail']


def test_ac5_documented_function_passes(tmp_path):
    documented = tmp_path / 'documented.py'
    documented.write_text(
        '"""Módulo de prueba."""\n\n\ndef public() -> int:\n    """Devuelve 1."""\n    return 1\n', encoding='utf-8'
    )

    assert run([documented])['status'] == 'pass'
