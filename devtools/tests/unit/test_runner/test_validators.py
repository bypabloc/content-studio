"""Ciclo 2 de la spec 003 (AC-1, AC-2): validador de tamaño por categoría con baseline."""

from __future__ import annotations

import json

from devtools.test_runner.validators import run, write_baseline

CONFIG = {
    'exclude': ['**/node_modules/**', 'server/data/**'],
    'categories': [
        {
            'name': 'tests',
            'include': ['**/tests/**', '**/test_*.py'],
            'extensions': ['.py'],
            'limits': {'lines': 800, 'bytes': 60000, 'lineLength': 300},
        },
        {
            'name': 'source',
            'include': ['**'],
            'extensions': ['.py'],
            'limits': {'lines': 300, 'bytes': 40000, 'lineLength': 300},
        },
    ],
}


def project(tmp_path, baseline=None):
    folder = tmp_path / 'tests' / 'validators'
    folder.mkdir(parents=True)
    (folder / 'file-size.json').write_text(json.dumps(CONFIG), encoding='utf-8')
    if baseline is not None:
        (folder / 'file-size.baseline.json').write_text(json.dumps(baseline), encoding='utf-8')
    return tmp_path


def write(root, name, lines):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'x = 1\n' * lines)
    return path


def test_ac1_source_with_301_lines_fails_naming_category_limit_and_measure(tmp_path):
    root = project(tmp_path)
    result = run([write(root, 'src/mod.py', 301)], root=root)

    assert result['status'] == 'fail'
    assert 'source' in result['detail'] and '300' in result['detail'] and '301' in result['detail']


def test_ac1_source_with_300_lines_passes(tmp_path):
    root = project(tmp_path)

    assert run([write(root, 'src/mod.py', 300)], root=root)['status'] == 'pass'


def test_ac1_test_with_801_lines_fails_with_the_tests_limit(tmp_path):
    root = project(tmp_path)
    result = run([write(root, 'server/tests/test_mod.py', 801)], root=root)

    assert result['status'] == 'fail'
    assert 'tests' in result['detail'] and '800' in result['detail']


def test_ac2_file_in_baseline_that_grows_fails(tmp_path):
    root = project(tmp_path, baseline={'src/big.py': {'lines': 320, 'bytes': 1920, 'lineLength': 5}})

    result = run([write(root, 'src/big.py', 321)], root=root)

    assert result['status'] == 'fail'
    assert '321' in result['detail']


def test_ac2_file_in_baseline_under_limit_passes_and_suggests_removing_it(tmp_path):
    root = project(tmp_path, baseline={'src/big.py': {'lines': 320, 'bytes': 1920, 'lineLength': 5}})

    result = run([write(root, 'src/big.py', 300)], root=root)

    assert result['status'] == 'pass'
    assert 'baseline' in result['detail']


def test_excluded_paths_are_not_measured(tmp_path):
    root = project(tmp_path)

    assert run([write(root, 'server/data/narration/big.py', 900)], root=root)['status'] == 'pass'


def test_files_outside_every_category_are_not_measured(tmp_path):
    root = project(tmp_path)

    assert run([write(root, 'notes/readme.md', 900)], root=root)['status'] == 'pass'


def test_write_baseline_records_only_the_files_over_their_limit(tmp_path):
    root = project(tmp_path)
    too_long = write(root, 'src/long.py', 301)
    short = write(root, 'src/short.py', 3)

    assert write_baseline([too_long, short], root=root) == 1
    saved = json.loads((root / 'tests/validators/file-size.baseline.json').read_text(encoding='utf-8'))
    assert saved == {'src/long.py': {'lines': 301, 'bytes': 1806, 'lineLength': 5}}
