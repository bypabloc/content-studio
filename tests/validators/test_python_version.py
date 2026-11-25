"""AC-1 y AC-2 de la spec 025: una sola versión de Python para server, CI e instalador (D-1, D-3, D-5)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / '.python-version'


def pinned() -> str:
    assert PIN.is_file(), 'falta .python-version en la raíz (spec 025, D-1)'
    return '.'.join(PIN.read_text(encoding='utf-8').strip().split('.')[:2])


def test_ac1_venv_runs_pinned_version():
    """AC-1: el intérprete que corre las pruebas (el venv de uv sync) es la versión de .python-version."""
    running = f'{sys.version_info[0]}.{sys.version_info[1]}'
    assert running == pinned(), f'el venv corre {running}; .python-version dice {pinned()}'


def test_ac2_versions_match():
    """AC-2: requires-python, la matriz de calidad.yml y PYTHON de prepare.rs siguen a .python-version."""
    version = pinned()
    server = (ROOT / 'server/pyproject.toml').read_text(encoding='utf-8')
    assert f'requires-python = ">={version}"' in server, f'server/pyproject.toml no dice >={version}'
    ci = (ROOT / '.github/workflows/calidad.yml').read_text(encoding='utf-8')
    mismatched = [v for v in re.findall(r"'(\d+\.\d+)'", ci) if v != version]
    assert not mismatched, f'calidad.yml usa {mismatched}; .python-version dice {version}'
    rust = (ROOT / 'client/src-tauri/src/bootstrap/prepare.rs').read_text(encoding='utf-8')
    found = re.search(r'pub const PYTHON: &str = "(\d+\.\d+)";', rust)
    assert found and found.group(1) == version, (
        f'prepare.rs PYTHON = {found and found.group(1)}; .python-version dice {version}'
    )
