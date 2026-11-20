"""`test-runner`: corre las etapas de calidad (spec 003, D-1 y D-6).

stdout = una línea JSON por etapa; stderr = resumen humano. Exit 0 si todas pasan, 1 si alguna falla, 2 con argumentos
inválidos. `--type=all` = GROUPS['all']: las etapas de calidad, las del client sin e2e (necesita Chromium) y budget.
guard-tdd se pide aparte (pre-push y CI).
"""

from __future__ import annotations

import json
import sys

from . import budget, changeset, client, guard_tdd, i18n, lint, spelling, tdd, typecheck, unit, validators
from .flags import parse

STAGES = {
    'lint': lint.run,
    'spelling': spelling.run,
    'validators': validators.run,
    'unit': unit.run,
    'typecheck': typecheck.run,
    'tdd': tdd.run,
    'guard-tdd': guard_tdd.run,
    'client-lint': client.lint,
    'client-typecheck': client.typecheck,
    'client-unit': client.unit,
    'tauri-check': client.tauri_check,
    'budget': budget.run,
    'e2e': client.e2e,
    'i18n': i18n.run,
}
GROUPS = {
    'all': [
        'lint',
        'spelling',
        'validators',
        'unit',
        'typecheck',
        'tdd',
        'client-lint',
        'client-typecheck',
        'client-unit',
        'budget',
    ],
}
FILE_STAGES = {'lint', 'spelling', 'validators', 'unit'}


USAGE = (
    'usage: python -m devtools test-runner [--type=<stages>] [--git-mode=changed|staged|unstaged|unmerged|all] '
    '[--files=a.py,b.py] [--write-baseline]\n'
    f'stages: {", ".join(STAGES)}; all = {", ".join(GROUPS["all"])}\n'
)


def main(argv: list[str]) -> int:
    """Entrada de `python -m devtools test-runner`: exit 0, 1 o 2 según el resultado."""
    if argv and argv[0] in ('-h', '--help'):
        print(USAGE, end='')
        return 0
    try:
        options = parse(argv, list(STAGES), GROUPS)
    except ValueError as error:
        print(f'test-runner: {error}', file=sys.stderr)
        return 2
    # Solo las etapas que miran archivos piden el changeset: `changed` y `unmerged` necesitan origin/dev.
    picked = changeset.files(options.git_mode, options.files) if FILE_STAGES & set(options.types) else []
    if options.write_baseline:
        print(
            json.dumps(
                {
                    'validators': validators.write_baseline(picked),
                    'unit': unit.write_baseline(),
                    'coverage': unit.write_coverage_baseline(),
                }
            )
        )
        return 0
    results = [STAGES[name](picked) for name in options.types]
    for result in results:
        print(json.dumps(result))
        print(f'{result["stage"]}: {result["status"]}', file=sys.stderr)
        if result['status'] == 'fail' and result['detail']:
            print(result['detail'], file=sys.stderr)
    return 1 if any(result['status'] == 'fail' for result in results) else 0
