"""Auditoría del espejo de client/tests/unit/src (spec 005, D-9)."""

from __future__ import annotations

import json

from devtools.test_runner import client_mirror


def _write(root, rel, text=''):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_a_module_without_its_mirror_test_is_reported(tmp_path):
    _write(tmp_path, 'client/src/app/Shell.tsx')

    assert client_mirror.problems(tmp_path) == [
        'client/src/app/Shell.tsx: no mirror test at client/tests/unit/src/app/Shell.test.tsx'
    ]


def test_the_mirror_test_satisfies_the_audit(tmp_path):
    _write(tmp_path, 'client/src/app/Shell.tsx')
    _write(tmp_path, 'client/tests/unit/src/app/Shell.test.tsx')

    assert client_mirror.problems(tmp_path) == []


def test_the_baseline_keeps_old_gaps_but_must_shrink(tmp_path):
    _write(tmp_path, 'client/src/app/Shell.tsx')
    _write(tmp_path, client_mirror.BASELINE, json.dumps({'untested': ['client/src/app/Shell.tsx']}))
    assert client_mirror.problems(tmp_path) == []

    _write(tmp_path, 'client/tests/unit/src/app/Shell.test.tsx')

    assert client_mirror.problems(tmp_path) == [
        f'client/src/app/Shell.tsx: has its mirror test now: remove it from {client_mirror.BASELINE}'
    ]


def test_components_ui_main_and_declarations_are_not_audited(tmp_path):
    _write(tmp_path, 'client/src/components/ui/button.tsx')
    _write(tmp_path, 'client/src/main.tsx')
    _write(tmp_path, 'client/src/shared/api/schema.d.ts')

    assert client_mirror.sources(tmp_path) == []
    assert client_mirror.problems(tmp_path) == []
