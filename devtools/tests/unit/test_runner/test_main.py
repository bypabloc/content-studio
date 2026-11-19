"""Ciclo 1 de la spec 003 (AC-8): esqueleto de `test-runner`."""

from __future__ import annotations

import json

from devtools.test_runner.main import main


def test_ac8_unknown_type_exits_2(capsys):
    assert main(['--type=foo']) == 2


def test_ac8_clean_lint_prints_one_json_line_exits_0(tmp_path, capsys):
    clean = tmp_path / 'clean.py'
    clean.write_text('"""Módulo de prueba."""\n\nx = 1\n', encoding='utf-8')

    assert main(['--type=lint', f'--files={clean}']) == 0

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])['stage'] == 'lint'
    assert json.loads(lines[0])['status'] == 'pass'
