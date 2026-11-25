"""Versiones de la spec 027: AC-1 sin rangos en los manifiestos; AC-5 la tabla de la regla coincide."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_MANIFESTS = ['package.json', 'client/package.json', 'tests/e2e/package.json']
CARGO_TOML = 'client/src-tauri/Cargo.toml'
RULE = '.agents/rules/frontend-stack.md'
EXACT_SEMVER = re.compile(r'^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$')
ROW = re.compile(r'^\|\s*`([^`]+)`\s*\|\s*(npm|crate)\s*\|\s*([^|\s]+)\s*\|')


def _cargo_tables() -> list[dict]:
    manifest = tomllib.loads((ROOT / CARGO_TOML).read_text(encoding='utf-8'))
    tables = [manifest.get('dependencies', {}), manifest.get('build-dependencies', {})]
    tables += [target.get('dependencies', {}) for target in manifest.get('target', {}).values()]
    return tables


def _cargo_version(spec: object) -> str:
    return spec.get('version', '') if isinstance(spec, dict) else str(spec)


def _package_json_problems(relative: str) -> list[str]:
    manifest = json.loads((ROOT / relative).read_text(encoding='utf-8'))
    problems = []
    for section in ('dependencies', 'devDependencies'):
        for name, version in manifest.get(section, {}).items():
            if not EXACT_SEMVER.match(version):
                problems.append(f'{relative} {section} {name} = {version!r}')
    return problems


def _cargo_problems() -> list[str]:
    problems = []
    for table in _cargo_tables():
        for name, spec in table.items():
            version = _cargo_version(spec)
            if not version.startswith('=') or not EXACT_SEMVER.match(version[1:]):
                problems.append(f'{CARGO_TOML} {name} = {version!r}')
    return problems


def _manifest_versions() -> dict[tuple[str, str], str]:
    found: dict[tuple[str, str], str] = {}
    for relative in PACKAGE_MANIFESTS:
        manifest = json.loads((ROOT / relative).read_text(encoding='utf-8'))
        for section in ('dependencies', 'devDependencies'):
            for name, version in manifest.get(section, {}).items():
                found[('npm', name)] = version
    for table in _cargo_tables():
        for name, spec in table.items():
            found[('crate', name)] = _cargo_version(spec).lstrip('=')
    return found


def _rule_rows() -> list[tuple[str, str, str]]:
    text = (ROOT / RULE).read_text(encoding='utf-8')
    section = text.split('## Versiones', 1)[1].split('\n## ', 1)[0]
    return [match.groups() for match in map(ROW.match, section.splitlines()) if match]


def test_ac1_versiones_exactas():
    problems = [p for relative in PACKAGE_MANIFESTS for p in _package_json_problems(relative)]
    problems += _cargo_problems()
    assert not problems, 'dependencias sin versión exacta:\n' + '\n'.join(problems)


def test_ac5_tabla_de_la_regla_coincide():
    rows = _rule_rows()
    assert rows, f'{RULE} no tiene la tabla «Versiones» con filas de paquete'
    manifest = _manifest_versions()
    problems = []
    for name, origin, version in rows:
        actual = manifest.get((origin, name))
        if actual is None:
            problems.append(f'{name} ({origin}): la tabla lo lista y ningún manifiesto lo declara')
        elif actual != version:
            problems.append(f'{name} ({origin}): la tabla dice {version}, el manifiesto {actual}')
    assert not problems, 'la tabla de la regla no coincide con los manifiestos:\n' + '\n'.join(problems)
