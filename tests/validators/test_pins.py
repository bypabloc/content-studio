"""Versiones exactas de los manifiestos (spec 027, AC-1): sin rangos en package.json ni en Cargo.toml."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_MANIFESTS = ['package.json', 'client/package.json', 'tests/e2e/package.json']
CARGO_TOML = 'client/src-tauri/Cargo.toml'
EXACT_SEMVER = re.compile(r'^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$')


def _package_json_problems(relative: str) -> list[str]:
    manifest = json.loads((ROOT / relative).read_text(encoding='utf-8'))
    problems = []
    for section in ('dependencies', 'devDependencies'):
        for name, version in manifest.get(section, {}).items():
            if not EXACT_SEMVER.match(version):
                problems.append(f'{relative} {section} {name} = {version!r}')
    return problems


def _cargo_problems() -> list[str]:
    manifest = tomllib.loads((ROOT / CARGO_TOML).read_text(encoding='utf-8'))
    tables = [manifest.get('dependencies', {}), manifest.get('build-dependencies', {})]
    tables += [target.get('dependencies', {}) for target in manifest.get('target', {}).values()]
    problems = []
    for table in tables:
        for name, spec in table.items():
            version = spec.get('version', '') if isinstance(spec, dict) else spec
            if not version.startswith('=') or not EXACT_SEMVER.match(version[1:]):
                problems.append(f'{CARGO_TOML} {name} = {version!r}')
    return problems


def test_ac1_versiones_exactas():
    problems = [p for relative in PACKAGE_MANIFESTS for p in _package_json_problems(relative)]
    problems += _cargo_problems()
    assert not problems, 'dependencias sin versión exacta:\n' + '\n'.join(problems)
