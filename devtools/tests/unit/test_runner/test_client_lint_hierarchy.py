"""Jerarquía de imports del client (spec 008, AC-3 y AC-10, D-4): oxlint la hace cumplir con overrides declarativos.

Cada fixture se copia con el `.oxlintrc.json` real a un client/ temporal (`client_lint_hierarchy.py`):
los `files` de los overrides son relativos a ese archivo. Lo que oxlint marca con la regla es un hallazgo.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from devtools.test_runner.client_lint_hierarchy import restricted_imports

FIXTURES = Path(__file__).resolve().parents[2] / 'fixtures' / 'client-hierarchy'

# Importes que D-4 prohíbe: un átomo que importa una molécula, una molécula que importa un organismo, un organismo que
# importa una feature, `shared/` que importa features, una feature que importa app, y npm o shadcn fuera de componentes.
FLAGGED = [
    'src/shared/components/atoms/flagged-molecule.ts',
    'src/shared/components/molecules/flagged-organism.ts',
    'src/shared/components/organisms/flagged-feature.ts',
    'src/features/queue/flagged-shadcn.ts',
    'src/features/queue/flagged-base-ui.ts',
    'src/features/queue/flagged-lucide.ts',
    'src/features/queue/flagged-uibox.ts',
    'src/features/queue/flagged-app.ts',
    'src/app/flagged-sonner.ts',
]

# Importes que D-4 permite: cada capa importa lo que le toca, y shadcn e npm solo dentro de shared/components.
ALLOWED = [
    'src/shared/components/atoms/allowed-atom.ts',
    'src/shared/components/molecules/allowed-molecule.ts',
    'src/features/queue/allowed-feature.ts',
    'src/app/allowed-app.ts',
    'src/shared/notify/allowed-notify.ts',
]


@pytest.mark.parametrize('name', FLAGGED)
def test_forbidden_import_is_flagged(tmp_path: Path, name: str) -> None:
    assert restricted_imports([name], FIXTURES, tmp_path).get(name), f'{name} should break the D-4 hierarchy'


@pytest.mark.parametrize('name', ALLOWED)
def test_permitted_import_is_not_flagged(tmp_path: Path, name: str) -> None:
    assert restricted_imports([name], FIXTURES, tmp_path).get(name) is None, f'{name} should be allowed by D-4'


def test_the_message_names_the_rule_of_the_layer(tmp_path: Path) -> None:
    """El aviso dice qué capa lo prohíbe, para que el agente sepa qué mover (textos en inglés, accionables)."""
    (message,) = restricted_imports(['src/shared/components/atoms/flagged-molecule.ts'], FIXTURES, tmp_path)[
        'src/shared/components/atoms/flagged-molecule.ts'
    ]

    assert 'Atoms import only atoms and shadcn' in message
