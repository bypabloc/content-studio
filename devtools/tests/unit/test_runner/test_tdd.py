"""Etapa tdd del test-runner: corre los tests efímeros de tdd/ y falla si alguno falla."""

from __future__ import annotations

from devtools.test_runner.tdd import run


def test_tdd_passing_test_passes(tmp_path):
    (tmp_path / 'devtools/tests/tdd').mkdir(parents=True)
    (tmp_path / 'devtools/tests/tdd/test_ok.py').write_text('def test_ok():\n    assert True\n', encoding='utf-8')

    assert run([], root=tmp_path)['status'] == 'pass'


def test_tdd_failing_test_fails_the_stage(tmp_path):
    (tmp_path / 'devtools/tests/tdd').mkdir(parents=True)
    (tmp_path / 'devtools/tests/tdd/test_bad.py').write_text('def test_bad():\n    assert False\n', encoding='utf-8')

    assert run([], root=tmp_path)['status'] == 'fail'


def test_tdd_without_folders_passes_without_running_pytest(tmp_path):
    assert run([], root=tmp_path) == {'stage': 'tdd', 'status': 'pass', 'detail': ''}
