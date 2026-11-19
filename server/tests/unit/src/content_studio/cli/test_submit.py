"""Flags de `studio` a parámetros de un trabajo (spec 004, D-6): los mismos nombres que usa el servicio."""

from __future__ import annotations

import pytest

from content_studio.cli import submit
from content_studio.music.parser import build_parser as music_parser
from content_studio.narration.parser import build_parser as narration_parser


def test_narration_flags_become_the_service_params():
    args = narration_parser().parse_args(['--model', 'qwen-0.6b', '--style', 'expert', '--text', 'Hola.'])

    params = submit.narration_params(args)

    assert (params['model'], params['style'], params['text']) == ('qwen-0.6b', 'expert', 'Hola.')
    assert 'evaluate' not in params  # un flag que no se pidió no viaja al trabajo


def test_narration_file_paths_become_strings():
    args = narration_parser().parse_args(['--model', 'qwen-0.6b', '--style', 'expert', '--file', 'guion.txt'])

    assert submit.narration_params(args)['file'] == ['guion.txt']


def test_music_keeps_the_style_list_and_the_duration_as_a_number():
    args = music_parser().parse_args(['--model', 'acestep', '--style', 'lofi-chill', 'corporate', '--duration', '15'])

    params = submit.music_params(args)

    assert (params['model'], params['style'], params['duration']) == ('acestep', ['lofi-chill', 'corporate'], 15.0)


def test_output_is_refused_because_the_job_folder_decides_where_it_goes():
    args = narration_parser().parse_args(
        ['--model', 'qwen-0.6b', '--style', 'expert', '--text', 'x', '--output', 'y.wav']
    )

    with pytest.raises(submit.UsageError):
        submit.narration_params(args)
