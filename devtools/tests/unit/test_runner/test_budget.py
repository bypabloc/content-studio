"""Etapa `budget` del test-runner (spec 005, D-9): el JS inicial del client en kB gzip, contra client/budget.json."""

from __future__ import annotations

import json
import os
import subprocess

from devtools.test_runner import budget


def _dist_with(root, sizes_by_name):
    assets = root / 'client' / 'dist' / 'assets'
    assets.mkdir(parents=True)
    for name, content in sizes_by_name.items():
        (assets / name).write_bytes(content)


def _budget(root, limit_kb):
    (root / 'client').mkdir(parents=True, exist_ok=True)
    (root / 'client' / 'budget.json').write_text(json.dumps({'initialJsGzipKb': limit_kb}), encoding='utf-8')


def test_measure_sums_the_gzip_size_of_each_js_asset(tmp_path):
    _dist_with(tmp_path, {'a.js': b'x' * 5000, 'b.css': b'y' * 5000})

    report = budget.measure(tmp_path / 'client' / 'dist')

    assert set(report['files']) == {'a.js'}
    assert 0 < report['total_kb'] < 1


def test_run_passes_when_the_initial_js_is_under_the_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(
        subprocess, 'run', lambda *a, **k: type('Done', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()
    )
    _dist_with(tmp_path, {'app.js': b'x' * 1000})
    _budget(tmp_path, 250)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'pass'
    assert (tmp_path / 'tmp' / 'budget' / 'report.json').is_file()


def test_run_fails_and_says_how_much_over_the_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(
        subprocess, 'run', lambda *a, **k: type('Done', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()
    )
    _dist_with(tmp_path, {'app.js': os.urandom(50000)})
    _budget(tmp_path, 0.1)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'kB' in result['detail']


def test_run_fails_when_the_build_fails(monkeypatch, tmp_path):
    failing = type('Done', (), {'returncode': 1, 'stdout': 'vite: error', 'stderr': ''})()
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: failing)
    _budget(tmp_path, 250)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'vite: error' in result['detail']


def test_run_fails_when_the_build_left_no_js(monkeypatch, tmp_path):
    """Sin JS en dist/assets el presupuesto no puede pasar con 0 kB: falla cerrado."""
    monkeypatch.setattr(
        subprocess, 'run', lambda *a, **k: type('Done', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()
    )
    _dist_with(tmp_path, {'app.css': b'x' * 1000})
    _budget(tmp_path, 250)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'no JS' in result['detail']
