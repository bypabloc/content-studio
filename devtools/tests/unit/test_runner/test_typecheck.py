"""Etapa typecheck del test-runner: mypy sobre los targets, con un fixture que rompe los tipos a propósito (AC-6)."""

from __future__ import annotations

from devtools.test_runner.typecheck import run


def test_ac6_clean_module_passes(tmp_path):
    (tmp_path / 'devtools').mkdir()
    (tmp_path / 'devtools' / 'clean.py').write_text('def f() -> int:\n    return 1\n', encoding='utf-8')

    assert run([], root=tmp_path, targets=['devtools'])['status'] == 'pass'


def test_ac6_type_error_fails_the_stage(tmp_path):
    (tmp_path / 'devtools').mkdir()
    (tmp_path / 'devtools' / 'bad.py').write_text("def f() -> int:\n    return 'x'\n", encoding='utf-8')

    result = run([], root=tmp_path, targets=['devtools'])

    assert result['status'] == 'fail'
    assert 'bad.py' in result['detail']
