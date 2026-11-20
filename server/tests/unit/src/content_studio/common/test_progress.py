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


def test_ac7_span_fraction_maps_a_step_into_the_span_of_the_whole_job():
    assert progress.span_fraction((0.0, 0.5), 1, 2) == 0.25
    assert progress.span_fraction((0.5, 1.0), 2, 2) == 1.0


def test_span_fraction_without_steps_does_not_divide_by_zero():
    assert progress.span_fraction((0.0, 1.0), 0, 0) == 0.0
