"""Flags de `test-runner`: `--type`, `--git-mode`, `--files` y `--write-baseline` (spec 003, D-1)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .changeset import GIT_MODES


@dataclass
class Options:
    """Opciones de `test-runner` ya validadas."""

    types: list[str]
    git_mode: str
    files: list[Path] | None
    write_baseline: bool = False


def parse(argv: list[str], known: list[str], groups: dict[str, list[str]] | None = None) -> Options:
    """Lanza ValueError con el motivo si un argumento no sirve (el runner sale con 2).

    `groups` nombra conjuntos de etapas (`all`): `--type=all` se expande y, sin `--type`, corre el grupo `all`.
    """
    groups = groups or {}
    types, git_mode, files, write_baseline = list(groups.get('all', known)), 'all', None, False
    for arg in argv:
        name, _, value = arg.partition('=')
        if name == '--type':
            types = [t for raw in value.split(',') for t in groups.get(raw, [raw])]
        elif name == '--git-mode':
            git_mode = value
        elif name == '--files':
            files = [Path(f) for f in value.split(',')]
        elif arg == '--write-baseline':
            write_baseline = True
        else:
            raise ValueError(f'unknown argument: {arg}')
    unknown = [t for t in types if t not in known]
    if unknown:
        raise ValueError(f'unknown type: {",".join(unknown)} (known: {",".join(known)})')
    if git_mode not in GIT_MODES:
        raise ValueError(f'unknown --git-mode: {git_mode} (known: {",".join(GIT_MODES)})')
    return Options(types, git_mode, files, write_baseline)
