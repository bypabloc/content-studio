"""Etapa unit del test-runner: auditoría del espejo (AC-3) y cobertura por archivo (AC-4)."""

from __future__ import annotations

import json

from devtools import paths
from devtools.test_runner import unit
from devtools.test_runner.unit import audit, check_coverage, in_scope, mirror_of, source_of, write_baseline

EMPTY = {'exempt': [], 'untested': []}


def tree(tmp_path, names, baseline=EMPTY):
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'')
    folder = tmp_path / 'tests' / 'validators'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'mirror.baseline.json').write_text(json.dumps(baseline), encoding='utf-8')
    return tmp_path


def problems_of(root):
    return audit(root)[0]


def test_ac3_orphan_test_fails_naming_it(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/tests/unit/src/content_studio/test_a.py',
            'server/tests/unit/src/content_studio/test_orphan.py',
        ],
    )

    problems = problems_of(root)

    assert len(problems) == 1
    assert 'test_orphan.py' in problems[0]


def test_ac3_new_module_without_test_fails_naming_it(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/src/content_studio/bar.py',
            'server/tests/unit/src/content_studio/test_a.py',
        ],
    )

    problems = problems_of(root)

    assert len(problems) == 1
    assert 'bar.py' in problems[0]


def test_ac3_test_outside_unit_src_integration_or_tdd_fails(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/tests/unit/src/content_studio/test_a.py',
            'server/tests/test_misc.py',
        ],
    )

    problems = problems_of(root)

    assert len(problems) == 1
    assert 'test_misc.py' in problems[0]


def test_ac3_mirrored_pair_and_integration_test_pass(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/tests/unit/src/content_studio/test_a.py',
            'server/tests/integration/test_flow.py',
        ],
    )

    assert problems_of(root) == []


def test_ac3_untested_module_listed_in_baseline_passes(tmp_path):
    root = tree(
        tmp_path,
        ['server/src/content_studio/bar.py'],
        baseline={'exempt': [], 'untested': ['server/src/content_studio/bar.py']},
    )

    assert problems_of(root) == []


def test_ac3_real_repo_mirror_passes():
    assert problems_of(paths.ROOT) == []


def report(percent_by_file):
    return {'files': {rel: {'summary': {'percent_covered': p}} for rel, p in percent_by_file.items()}}


def test_ac4_coverage_per_file():
    measured = report({'server/src/content_studio/a.py': 70.0, 'server/src/content_studio/b.py': 80.0})

    assert check_coverage(measured, ['server/src/content_studio/a.py'], []) == [
        'server/src/content_studio/a.py: 70% covered (min 80%)'
    ]
    assert check_coverage(measured, ['server/src/content_studio/b.py'], []) == []


def test_ac4_file_missing_from_the_report_counts_as_zero():
    assert check_coverage(report({}), ['server/src/content_studio/c.py'], []) == [
        'server/src/content_studio/c.py: 0% covered (min 80%)'
    ]


def test_ac4_file_in_coverage_baseline_is_not_checked():
    measured = report({'server/src/content_studio/a.py': 10.0})

    assert check_coverage(measured, ['server/src/content_studio/a.py'], ['server/src/content_studio/a.py']) == []


def test_mirror_maps_server_and_devtools_both_ways():
    assert mirror_of('server/src/content_studio/a/b.py') == 'server/tests/unit/src/content_studio/a/test_b.py'
    assert mirror_of('devtools/worktree.py') == 'devtools/tests/unit/test_worktree.py'
    assert source_of('server/tests/unit/src/content_studio/a/test_b.py') == 'server/src/content_studio/a/b.py'
    assert source_of('devtools/tests/unit/test_runner/test_main.py') == 'devtools/test_runner/main.py'


def test_in_scope_keeps_product_and_devtools_and_skips_engines_and_tests():
    assert in_scope('server/src/content_studio/narration/tts.py')
    assert in_scope('server/src/content_studio/cli/main.py')
    assert in_scope('devtools/rules.py')
    for rel in (
        'server/src/content_studio/narration/engines/qwen.py',
        'devtools/tests/unit/test_rules.py',
        'server/src/content_studio/a/__init__.py',
        'README.md',
    ):
        assert not in_scope(rel), rel


def test_run_passes_when_pytest_and_coverage_are_clean(tmp_path, monkeypatch):
    root = tree(tmp_path, ['server/src/content_studio/a.py', 'server/tests/unit/src/content_studio/test_a.py'])
    monkeypatch.setattr(unit, 'coverage_report', lambda _root: (0, report({'server/src/content_studio/a.py': 85.0})))

    assert unit.run([root / 'server/src/content_studio/a.py'], root=root)['status'] == 'pass'


def test_run_fails_when_pytest_fails(tmp_path, monkeypatch):
    root = tree(tmp_path, ['server/src/content_studio/a.py', 'server/tests/unit/src/content_studio/test_a.py'])
    monkeypatch.setattr(unit, 'coverage_report', lambda _root: (1, report({})))

    result = unit.run([], root=root)

    assert result['status'] == 'fail'
    assert 'pytest failed (exit 1)' in result['detail']


def test_write_baseline_lists_only_modules_without_a_test(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/src/content_studio/b.py',
            'server/tests/unit/src/content_studio/test_a.py',
        ],
    )

    assert write_baseline(root) == 1
    assert unit.load(root)['untested'] == ['server/src/content_studio/b.py']
