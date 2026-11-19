"""Reglas de .agents/rules/codigo-python.md que se pueden comprobar: sintaxis 3.10, dependencias y
la sincronía de reglas y skills entre .agents/ y .claude/ (agent-config-testing.md)."""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

from devtools import rules

ROOT = Path(__file__).resolve().parents[2]
HOOKS = [ROOT / '.claude/hooks']


def files() -> list[Path]:
    sources = [
        ROOT / 'cli.py',
        *(ROOT / 'server/src').rglob('*.py'),
        *(ROOT / 'server/tests').rglob('*.py'),
        *(ROOT / 'devtools').rglob('*.py'),
        *(ROOT / 'tests').rglob('*.py'),
        *(ROOT / '.claude/hooks/tests').rglob('*.py'),
    ]
    return sorted(sources + [p for h in HOOKS for p in h.glob('*.py')])


FILES = files()


def name(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


@pytest.mark.parametrize('path', FILES, ids=name)
def test_syntax_310(path):
    """compile() con el intérprete de la matriz de CI y ast con la gramática de 3.10 (CosyVoice corre en 3.10)."""
    source = path.read_text(encoding='utf-8')
    compile(source, str(path), 'exec')
    ast.parse(source, str(path), feature_version=(3, 10))


def test_code_only_in_src():
    """narration/ y music/ son carpetas de datos; en la raíz solo queda el shim cli.py."""
    loose = [*ROOT.glob('*.py'), *ROOT.glob('narration/*.py'), *ROOT.glob('music/*.py')]
    assert [name(p) for p in loose] == ['cli.py']


def test_ac2_product_in_server():
    """AC-2: el producto vive en server/src/content_studio; en la raíz, cli.py es el único .py."""
    assert not (ROOT / 'src').exists()
    assert (ROOT / 'server/src/content_studio/paths.py').is_file()
    assert [name(p) for p in ROOT.glob('*.py')] == ['cli.py']
    assert not [p for d in ('narration', 'music') for p in (ROOT / 'server/data' / d).glob('*.py')]


def test_rules_and_skills_synced():
    """Cada regla y skill de .claude/ tiene el cuerpo de su fuente en .agents/ (devtools rules --sync)."""
    assert rules.differences(ROOT) == []


OLD_PATHS = (
    r'(?<![\w/.-])src/content_studio',
    r'PYTHONPATH=src\b',
    r'content_studio\.devtools',
    r'(?<!server/data/)narration/\.venv',
    r'(?<!server/data/)music/models',
)
# Historial y specs se quedan como están; test_move_data crea el árbol viejo a propósito; hatch es relativo a server/.
OUTSIDE_CHECK = ('tests/validators/test_structure.py', 'devtools/tests/unit/test_move_data.py', 'server/pyproject.toml')


def test_ac7_without_old_paths():
    """AC-7: lo versionado (sin historial ni specs) no nombra src/, content_studio.devtools
    ni los datos fuera de server/data/."""
    versioned = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    failures = []
    for path in versioned.split():
        history = path.startswith(('docs/research/', 'docs/specs/')) and not path.startswith('docs/specs/_plantilla/')
        if history or path in OUTSIDE_CHECK or not (ROOT / path).is_file():
            continue
        text = (ROOT / path).read_text(encoding='utf-8', errors='ignore')
        failures += [f'{path}: {p}' for p in OLD_PATHS if re.search(p, text)]
    assert failures == []


def test_dependencies_cli_equal_a_pyproject():
    deps = r'dependencies = (\[.*?\])'
    header = re.search(deps, (ROOT / 'cli.py').read_text(encoding='utf-8'))[1]
    project = re.search(deps, (ROOT / 'server/pyproject.toml').read_text(encoding='utf-8'))[1]
    assert ast.literal_eval(header) == ast.literal_eval(project)
