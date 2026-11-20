"""Etiquetas nativas fuera de los átomos (spec 008, AC-2 y AC-4, D-5): la etapa `ui-structure` de devtools."""

from __future__ import annotations

from pathlib import Path

import pytest

from devtools import paths
from devtools.test_runner import ui_structure
from devtools.test_runner.ui_structure import Finding, _show, check_ui_structure, is_exempt, run

FIXTURES = Path(__file__).resolve().parents[2] / 'fixtures' / 'ui-structure'


def test_flags_native_tags_outside_atoms_and_shadcn():
    """Un elemento JSX en minúscula, un createElement con cadena y un <Tag> con constante fallan fuera de átomos."""
    files = [
        FIXTURES / 'features' / 'flagged-div.tsx',
        FIXTURES / 'features' / 'flagged-button.tsx',
        FIXTURES / 'molecules' / 'flagged-svg.tsx',
        FIXTURES / 'app' / 'flagged-create-element.tsx',
        FIXTURES / 'features' / 'flagged-dynamic-tag.tsx',
    ]

    findings = check_ui_structure(files, base=FIXTURES)

    assert [(finding.tag, finding.line) for finding in findings] == [
        ('div', 2),
        ('button', 2),
        ('svg', 2),
        ('span', 4),
        ('h1', 4),
    ]


def test_native_tags_are_allowed_inside_atoms_and_shadcn():
    files = [FIXTURES / 'atoms' / 'allowed-native.tsx', FIXTURES / 'shadcn' / 'allowed-native.tsx']

    assert check_ui_structure(files, base=FIXTURES) == []


def test_components_and_generic_arrows_are_not_native_tags():
    """<UIStack> es un componente y <T,> es un genérico de TypeScript: ninguno es una etiqueta nativa."""
    assert check_ui_structure([FIXTURES / 'features' / 'allowed-components.tsx'], base=FIXTURES) == []


def test_only_folders_named_atoms_or_shadcn_are_exempt():
    assert is_exempt(FIXTURES / 'atoms' / 'x.tsx', FIXTURES)
    assert is_exempt(FIXTURES / 'shadcn' / 'x.tsx', FIXTURES)
    assert not is_exempt(FIXTURES / 'features' / 'atoms.tsx', FIXTURES)
    assert not is_exempt(FIXTURES / 'features' / 'x.tsx', FIXTURES)


def test_message_names_the_file_line_and_tag():
    finding = Finding(path='client/src/features/queue/JobRow.tsx', line=14, tag='button')

    assert finding.message() == (
        'client/src/features/queue/JobRow.tsx:14: native <button> outside atoms. '
        'Use a component from shared/components (UIButton, UIIconButton) or add one.'
    )


def test_ac4_precommit_runs_ui_structure_next_to_the_client_gates():
    """El pre-commit corre la etapa junto a las del client cuando hay archivos de client/ en el staging (AC-4)."""
    hook = (paths.ROOT / '.git-hooks' / 'pre-commit').read_text(encoding='utf-8')
    client_gate = next(line for line in hook.splitlines() if 'client-lint,client-typecheck,client-unit' in line)

    assert 'ui-structure' in client_gate


def test_the_stage_passes_on_the_real_client_tree():
    """La etapa revisa todo client/src: el árbol real no tiene etiquetas nativas fuera de los átomos (AC-2)."""
    assert run([]) == {'stage': 'ui-structure', 'status': 'pass', 'detail': ''}


def test_the_stage_fails_with_a_message_when_bun_is_missing(monkeypatch):
    def missing_bun(*args, **kwargs):
        raise FileNotFoundError('bun')

    monkeypatch.setattr(ui_structure.subprocess, 'run', missing_bun)

    result = run([])

    assert result['status'] == 'fail'
    assert 'bun is not in PATH' in result['detail']


def test_a_failing_script_raises_its_own_error(monkeypatch):
    class Failed:
        returncode = 2
        stdout = ''
        stderr = 'ui-structure: cannot read file'

    monkeypatch.setattr(ui_structure.subprocess, 'run', lambda *args, **kwargs: Failed())

    with pytest.raises(RuntimeError, match='cannot read file'):
        check_ui_structure([FIXTURES / 'features' / 'flagged-div.tsx'], base=FIXTURES)


def test_paths_outside_the_repo_are_shown_as_given(tmp_path):
    assert _show(tmp_path / 'x.tsx', paths.ROOT) == (tmp_path / 'x.tsx').as_posix()
