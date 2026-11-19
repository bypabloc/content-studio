"""Entrada `python -m devtools`: despacho, errores y ayuda."""

from __future__ import annotations

import subprocess
import sys

from devtools import paths
from devtools.__main__ import main as devtools


def test_dispatch_and_errors():
    assert devtools([]) == 0
    assert devtools(['nothing']) == 2
    assert devtools(['worktree']) == 2
    assert devtools(['gpu-turn', 'run', '--', 'x']) == 2  # missing --job


def test_ac3_help_list_commands():
    """AC-3: devtools vive en la raíz; `python -m devtools --help` lista sus comandos y sale con 0."""
    r = subprocess.run([sys.executable, '-m', 'devtools', '--help'], cwd=paths.ROOT, capture_output=True, text=True)
    assert r.returncode == 0
    assert all(c in r.stderr for c in ('worktree', 'gpu-turn', 'agent-context', 'rules', 'move-data'))
