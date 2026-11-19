"""Flags de test-runner: tipos conocidos, modos de git y argumentos inválidos (exit 2 en main)."""

from __future__ import annotations

from pathlib import Path

import pytest

from devtools.test_runner.flags import parse

KNOWN = ['lint', 'validators']


def test_type_list_splits_on_commas():
    assert parse(['--type=lint,validators'], KNOWN).types == ['lint', 'validators']


def test_without_type_runs_the_all_group():
    assert parse([], KNOWN, groups={'all': KNOWN}).types == KNOWN


def test_all_expands_to_its_group_and_guard_is_not_in_it():
    options = parse(['--type=all'], [*KNOWN, 'guard'], groups={'all': KNOWN})

    assert options.types == KNOWN


def test_files_and_git_mode_are_read():
    options = parse(['--git-mode=staged', '--files=a.py,b.py'], KNOWN)

    assert options.git_mode == 'staged'
    assert options.files == [Path('a.py'), Path('b.py')]


def test_write_baseline_flag_is_read():
    assert parse(['--write-baseline'], KNOWN).write_baseline is True


@pytest.mark.parametrize(
    'argv',
    [['--type=foo'], ['--git-mode=whatever'], ['--unknown=1']],
)
def test_invalid_arguments_raise_value_error(argv):
    with pytest.raises(ValueError):
        parse(argv, KNOWN)
