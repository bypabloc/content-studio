"""Parser de narración: `--profile` elige el perfil de voz propia (spec 010, D-1); `--ref` deja de ser un flag."""

from __future__ import annotations

import pytest

from content_studio.narration.parser import build_parser


def test_profile_flag():
    args = build_parser().parse_args(['--text', 'Hola.', '--profile', 'spec-010'])

    assert args.profile == 'spec-010'


def test_profile_defaults_to_the_default_profile():
    assert build_parser().parse_args(['--text', 'Hola.']).profile == 'default'


def test_ref_is_no_longer_a_flag():
    with pytest.raises(SystemExit):
        build_parser().parse_args(['--text', 'Hola.', '--ref', 'clara.wav'])
