"""Protocolo de progreso (spec 004, D-4): `@@progress {json}` en stdout, con p en 0–1 y una etapa."""

from __future__ import annotations

from content_studio.common import progress


def test_emit_prints_the_progress_line(capsys):
    progress.emit(0.42, 'block 3/7')

    assert capsys.readouterr().out == '@@progress {"p": 0.42, "stage": "block 3/7"}\n'


def test_parse_reads_back_what_emit_wrote(capsys):
    progress.emit(0.5, 'x')
    line = capsys.readouterr().out.rstrip('\n')

    assert progress.parse(line) == {'p': 0.5, 'stage': 'x'}


def test_parse_ignores_other_lines_and_malformed_progress():
    assert progress.parse('Seed: 123') is None
    assert progress.parse('@@progress {no json') is None
    assert progress.parse('@@progress [1, 2]') is None
