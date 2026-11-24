"""Etapa `budget` (spec 005, D-9): el JS de arranque del client, en kB gzip, contra client/budget.json."""

from __future__ import annotations

import json
import os
import subprocess

from devtools.test_runner import budget


def _dist_with(root, sizes_by_name, entry=(), preload=()):
    """Escribe dist/assets y un index.html que carga `entry` y precarga `preload` (nombres de archivo)."""
    assets = root / 'client' / 'dist' / 'assets'
    assets.mkdir(parents=True)
    for name, content in sizes_by_name.items():
        (assets / name).write_bytes(content)
    tags = [f'<script type="module" crossorigin src="/assets/{name}"></script>' for name in entry]
    tags += [f'<link rel="modulepreload" crossorigin href="/assets/{name}">' for name in preload]
    (root / 'client' / 'dist' / 'index.html').write_text('<!doctype html>' + ''.join(tags), encoding='utf-8')


def _budget(root, limit_kb):
    (root / 'client').mkdir(parents=True, exist_ok=True)
    (root / 'client' / 'budget.json').write_text(json.dumps({'initialJsGzipKb': limit_kb}), encoding='utf-8')


def _built(monkeypatch):
    monkeypatch.setattr(
        subprocess, 'run', lambda *a, **k: type('Done', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()
    )


def test_measure_counts_the_entry_and_its_preloads_but_not_the_lazy_chunks(tmp_path):
    _dist_with(
        tmp_path,
        {'entry.js': b'x' * 5000, 'vendor.js': b'y' * 5000, 'lazy.js': os.urandom(50000)},
        entry=['entry.js'],
        preload=['vendor.js'],
    )

    report = budget.measure(tmp_path / 'client' / 'dist')

    assert set(report['files']) == {'entry.js', 'vendor.js'}
    assert 0 < report['total_kb'] < 1


def test_measure_ignores_the_css(tmp_path):
    _dist_with(tmp_path, {'entry.js': b'x' * 5000, 'app.css': b'y' * 5000}, entry=['entry.js'])

    report = budget.measure(tmp_path / 'client' / 'dist')

    assert set(report['files']) == {'entry.js'}


def test_run_passes_when_the_initial_js_is_under_the_budget(monkeypatch, tmp_path):
    _built(monkeypatch)
    _dist_with(tmp_path, {'app.js': b'x' * 1000}, entry=['app.js'])
    _budget(tmp_path, 250)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'pass'
    assert (tmp_path / 'tmp' / 'budget' / 'report.json').is_file()


def test_run_fails_and_says_how_much_over_the_budget(monkeypatch, tmp_path):
    _built(monkeypatch)
    _dist_with(tmp_path, {'app.js': os.urandom(50000)}, entry=['app.js'])
    _budget(tmp_path, 0.1)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'kB' in result['detail']


def test_run_passes_when_only_a_lazy_chunk_is_big(monkeypatch, tmp_path):
    """Una pantalla diferida (import()) pesa en su chunk, no en el arranque: no cuenta contra el presupuesto."""
    _built(monkeypatch)
    _dist_with(tmp_path, {'app.js': b'x' * 1000, 'screen.js': os.urandom(50000)}, entry=['app.js'])
    _budget(tmp_path, 5)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'pass'


def test_run_fails_when_the_build_fails(monkeypatch, tmp_path):
    failing = type('Done', (), {'returncode': 1, 'stdout': 'vite: error', 'stderr': ''})()
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: failing)
    _budget(tmp_path, 250)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'vite: error' in result['detail']


def test_run_fails_when_the_build_left_no_js(monkeypatch, tmp_path):
    """Sin script de entrada en index.html el presupuesto no puede pasar con 0 kB: falla cerrado."""
    _built(monkeypatch)
    _dist_with(tmp_path, {'app.css': b'x' * 1000})
    _budget(tmp_path, 250)

    result = budget.run([], root=tmp_path)

    assert result['status'] == 'fail'
    assert 'no JS' in result['detail']
