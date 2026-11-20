"""Etiquetas nativas fuera de los átomos (spec 008, AC-2 y AC-4, D-5): la etapa `ui-structure` de devtools."""

from __future__ import annotations

from pathlib import Path

from devtools import paths
from devtools.test_runner.ui_structure import Finding, check_ui_structure, is_exempt

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
