"""Ciclo 4 de la spec 003 (AC-3): auditoría del espejo de tests, con huérfanos y tests fuera de lugar."""

from __future__ import annotations

import json

from devtools import paths
from devtools.test_runner.unit import run

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


def test_ac3_orphan_test_fails_naming_it(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/tests/unit/src/content_studio/test_a.py',
            'server/tests/unit/src/content_studio/test_orphan.py',
        ],
    )

    result = run([], root=root)

    assert result['status'] == 'fail'
    assert 'test_orphan.py' in result['detail']


def test_ac3_new_module_without_test_fails_naming_it(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/src/content_studio/bar.py',
            'server/tests/unit/src/content_studio/test_a.py',
        ],
    )

    result = run([], root=root)

    assert result['status'] == 'fail'
    assert 'bar.py' in result['detail']


def test_ac3_test_outside_unit_src_integration_or_tdd_fails(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/tests/unit/src/content_studio/test_a.py',
            'server/tests/test_misc.py',
        ],
    )

    result = run([], root=root)

    assert result['status'] == 'fail'
    assert 'test_misc.py' in result['detail']


def test_ac3_mirrored_pair_and_integration_test_pass(tmp_path):
    root = tree(
        tmp_path,
        [
            'server/src/content_studio/a.py',
            'server/tests/unit/src/content_studio/test_a.py',
            'server/tests/integration/test_flow.py',
        ],
    )

    assert run([], root=root)['status'] == 'pass'


def test_ac3_untested_module_listed_in_baseline_passes(tmp_path):
    root = tree(
        tmp_path,
        ['server/src/content_studio/bar.py'],
        baseline={'exempt': [], 'untested': ['server/src/content_studio/bar.py']},
    )

    assert run([], root=root)['status'] == 'pass'


def test_ac3_real_repo_passes():
    assert run([], root=paths.ROOT)['status'] == 'pass'
