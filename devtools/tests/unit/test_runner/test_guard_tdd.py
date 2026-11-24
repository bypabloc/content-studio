"""Etapa guard-tdd del test-runner: falla mientras quede algún test efímero en tdd/ (AC-7)."""

from __future__ import annotations

from devtools.test_runner.guard_tdd import run


def test_ac7_leftover_tdd_test_fails_naming_it(tmp_path):
    (tmp_path / 'server/tests/tdd').mkdir(parents=True)
    (tmp_path / 'server/tests/tdd/test_pieza.py').write_text('def test_x():\n    pass\n', encoding='utf-8')

    result = run([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'server/tests/tdd/test_pieza.py' in result['detail']


def test_ac7_without_tdd_tests_passes(tmp_path):
    (tmp_path / 'server/tests/unit').mkdir(parents=True)
    (tmp_path / 'server/tests/unit/test_ok.py').write_text('def test_ok():\n    pass\n', encoding='utf-8')

    assert run([], root=tmp_path) == {'stage': 'guard-tdd', 'status': 'pass', 'detail': ''}
