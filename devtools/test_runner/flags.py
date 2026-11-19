"""Flags de `test-runner`: `--type`, `--git-mode` y `--files` (spec 003, D-1)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .changeset import GIT_MODES


@dataclass
class Options:
    types: list[str]
    git_mode: str
    files: list[Path] | None


def parse(argv: list[str], known: list[str]) -> Options:
    """Lanza ValueError con el motivo si un argumento no sirve (el runner sale con 2)."""
    types, git_mode, files = list(known), 'all', None
    for arg in argv:
        name, _, value = arg.partition('=')
        if name == '--type':
            types = value.split(',')
        elif name == '--git-mode':
            git_mode = value
        elif name == '--files':
            files = [Path(f) for f in value.split(',')]
        else:
            raise ValueError(f'unknown argument: {arg}')
    unknown = [t for t in types if t not in known]
    if unknown:
        raise ValueError(f'unknown type: {",".join(unknown)} (known: {",".join(known)})')
    if git_mode not in GIT_MODES:
        raise ValueError(f'unknown --git-mode: {git_mode} (known: {",".join(GIT_MODES)})')
    return Options(types, git_mode, files)
