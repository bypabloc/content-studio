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
HOOKS = [ROOT / '.claude/hooks', ROOT / '.agents/hooks']


def files() -> list[Path]:
    sources = [
        *(ROOT / 'server/src').rglob('*.py'),
        *(ROOT / 'server/tests').rglob('*.py'),
        *(ROOT / 'devtools').rglob('*.py'),
        *(ROOT / 'tests').rglob('*.py'),
        *(ROOT / '.claude/hooks/tests').rglob('*.py'),
        *(ROOT / '.agents/hooks/tests').rglob('*.py'),
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
    """narration/ y music/ son carpetas de datos; el código vive solo en server/src (la raíz no tiene .py)."""
    loose = [*ROOT.glob('*.py'), *ROOT.glob('narration/*.py'), *ROOT.glob('music/*.py')]
    assert [name(p) for p in loose] == []


def test_ac2_product_in_server():
    """AC-2: el producto vive en server/src/content_studio; en la raíz no queda ningún .py."""
    assert not (ROOT / 'src').exists()
    assert (ROOT / 'server/src/content_studio/paths.py').is_file()
    assert [name(p) for p in ROOT.glob('*.py')] == []
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


def test_no_py_at_root():
    """AC-9: la raíz no tiene .py: el CLI es `studio` (server/src/content_studio/cli/main.py)."""
    assert list(ROOT.glob('*.py')) == []


def test_ac10_no_legacy_recording():
    """AC-10: lo versionado (sin docs ni uv.lock, que es generado) no nombra grabar/, questionary ni rich: la
    grabación es la UI. La palabra «grabar» sola sigue en los textos de la UI."""
    legacy = re.compile(r'narration[./]grabar|grabar/|questionary|\brich\b')
    versioned = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    failures = []
    for path in versioned.split():
        if (
            path.endswith('.md')
            or path.startswith('docs/')
            or path in ('uv.lock', 'tests/validators/test_structure.py')
        ):
            continue
        if not (ROOT / path).is_file():
            continue
        text = (ROOT / path).read_text(encoding='utf-8', errors='ignore')
        failures += [f'{path}: {m.group(0)}' for m in legacy.finditer(text)]
    assert failures == []


def test_ac10_no_whisper_cli():
    """AC-10: el código no llama al comando `whisper` (openai-whisper): la evaluación y el chequeo de tomas usan el
    servicio de faster-whisper (spec 013, D-7)."""
    cli = re.compile(r"""which\(\s*['"]whisper['"]\s*\)|\[\s*['"]whisper['"]\s*,""")
    hits = [
        f'{path.relative_to(ROOT)}: {m.group(0)}'
        for path in (ROOT / 'server/src').rglob('*.py')
        for m in cli.finditer(path.read_text(encoding='utf-8'))
    ]
    assert hits == []


def _guard_matchers(hooks: dict) -> list[str]:
    """Los matchers de PreToolUse que ejecutan computer_use_guard.py."""
    return [
        entry.get('matcher', '')
        for entry in hooks.get('PreToolUse', [])
        if any('computer_use_guard.py' in hook.get('command', '') for hook in entry.get('hooks', []))
    ]


def test_ac3_computer_use_guard_wired_for_every_agent():
    """Spec 024: el guard de Computer Use corre en Claude Code, Codex y Antigravity, con rutas del checkout."""
    import json

    claude = json.loads((ROOT / '.claude/settings.json').read_text(encoding='utf-8'))['hooks']
    codex = json.loads((ROOT / '.codex/hooks.json').read_text(encoding='utf-8'))['hooks']
    antigravity = json.loads((ROOT / '.agents/hooks.json').read_text(encoding='utf-8'))
    groups = {'claude': claude, 'codex': codex, 'antigravity': next(iter(_named(antigravity)), {})}
    expected = {
        'claude': ['mcp__computer-use__screenshot', 'mcp__remote-devices__computer_click'],
        'codex': ['mcp__node_repl__js', 'exec', 'js'],
        'antigravity': ['computer_click'],
    }
    for agent, names in expected.items():
        matchers = _guard_matchers(groups[agent])
        assert matchers, f'{agent}: no PreToolUse runs computer_use_guard.py'
        assert all(any(re.search(m, n) for m in matchers) for n in names), f'{agent}: {matchers} misses {names}'
        assert not any(re.search(m, 'Bash') for m in matchers), f'{agent}: the matcher also catches Bash'
    for text in (ROOT / '.claude/settings.json', ROOT / '.codex/hooks.json', ROOT / '.agents/hooks.json'):
        assert not re.search(r'[A-Za-z]:[\\/]Users', text.read_text(encoding='utf-8')), f'{text}: absolute path'


def _named(antigravity: dict) -> list[dict]:
    """Antigravity agrupa sus hooks por nombre: el grupo que tenga PreToolUse con el guard."""
    return [group for group in antigravity.values() if _guard_matchers(group)]


TEMPLATE = ROOT / 'docs/specs/_plantilla'
TEMPLATE_FILES = (
    'README.md',
    '01-contexto-y-decision.md',
    '02-diseno.md',
    '03-verificacion-final.md',
    'fases/1-tema/plan-tdd.md',
    'fases/1-tema/archivos.md',
    'fases/1-tema/commits.md',
)


def test_spec_template_has_phase_folders():
    """plan-format.md §2: la plantilla trae los archivos raíz y una carpeta de fase (plan-tdd, archivos, commits),
    sin el viejo 02-plan.md, y la regla la nombra completa."""
    found = sorted(p.relative_to(TEMPLATE).as_posix() for p in TEMPLATE.rglob('*.md'))
    assert found == sorted(TEMPLATE_FILES)
    rule = (ROOT / '.agents/rules/plan-format.md').read_text(encoding='utf-8')
    assert [name for name in ('02-diseno.md', 'plan-tdd.md', 'archivos.md', 'commits.md') if name not in rule] == []
    assert '02-plan.md' not in rule


def test_spec_template_fixed_block_links_resolve():
    """El bloque fijo va en los archivos raíz y en cada plan-tdd.md, y sus enlaces a docs/process/ existen."""
    with_block = [f for f in TEMPLATE_FILES if not f.endswith(('archivos.md', 'commits.md'))]
    broken = []
    for name in with_block:
        path = TEMPLATE / name
        text = path.read_text(encoding='utf-8')
        assert '**Datos del usuario: solo los que crea esta spec**' in text, name
        for link in re.findall(r'\]\(([./]+process/[^)]+)\)', text):
            if not (path.parent / link).resolve().is_file():
                broken.append(f'{name}: {link}')
    assert broken == []


def test_spec_template_without_stale_commands():
    """La plantilla usa los comandos vigentes: studio no acepta --output/--salida ni hay cli.py en la raíz."""
    stale = re.compile(r'--salida|--output|python cli\.py|contexto-agentes|turno-gpu run|--trabajo=|02-plan\.md')
    hits = [
        f'{name}: {m.group(0)}'
        for name in TEMPLATE_FILES
        for m in stale.finditer((TEMPLATE / name).read_text(encoding='utf-8'))
    ]
    assert hits == []
