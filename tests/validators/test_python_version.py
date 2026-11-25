"""AC-1 y AC-2 de la spec 025: una sola versión de Python para server, CI e instalador (D-1, D-3, D-5)."""

from __future__ import annotations

import re
import sys
import tomllib
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


def locked_versions() -> dict[str, str]:
    lock = tomllib.loads((ROOT / 'uv.lock').read_text(encoding='utf-8'))
    return {package['name']: package['version'] for package in lock['package']}


def direct_requirements() -> list[tuple[str, str, str | None]]:
    """(archivo, nombre, cota inferior) de cada dependencia directa del server y de la raíz del workspace."""
    found = []
    for rel in ('server/pyproject.toml', 'pyproject.toml'):
        data = tomllib.loads((ROOT / rel).read_text(encoding='utf-8'))
        specs = list(data.get('project', {}).get('dependencies', []))
        for group in data.get('dependency-groups', {}).values():
            specs += [spec for spec in group if isinstance(spec, str)]
        for spec in specs:
            match = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9._-]*)(?:>=([0-9][\w.]*))?', spec)
            assert match, f'{rel}: no se lee la dependencia {spec!r}'
            found.append((rel, match.group(1), match.group(2)))
    return found


def test_ac4_bounds_match_lock():
    """AC-4: la cota inferior de cada dependencia directa es la versión del uv.lock (D-4)."""
    locked = locked_versions()
    problems = []
    for rel, name, bound in direct_requirements():
        key = re.sub(r'[-_.]+', '-', name).lower()
        if key not in locked:
            problems.append(f'{rel}: {name} no está en uv.lock')
        elif bound != locked[key]:
            problems.append(f'{rel}: {name} >={bound or "(sin cota)"}, uv.lock tiene {locked[key]}')
    assert not problems, '\n'.join(problems)
