"""`test-runner`: corre las etapas de calidad (spec 003, D-1 y D-6).

stdout = una línea JSON por etapa; stderr = resumen humano. Exit 0 si todas pasan, 1 si alguna falla, 2 con argumentos
inválidos. `--type=all` = lint, spelling, validators, typecheck, unit y tdd; guard-tdd se pide aparte (pre-push y CI).
"""

from __future__ import annotations

import json
import sys

from . import changeset, guard_tdd, lint, spelling, tdd, typecheck, unit, validators
from .flags import parse

STAGES = {
    'lint': lint.run,
    'spelling': spelling.run,
    'validators': validators.run,
    'unit': unit.run,
    'typecheck': typecheck.run,
    'tdd': tdd.run,
    'guard-tdd': guard_tdd.run,
}
GROUPS = {'all': ['lint', 'spelling', 'validators', 'unit', 'typecheck', 'tdd']}
FILE_STAGES = {'lint', 'spelling', 'validators', 'unit'}


def main(argv: list[str]) -> int:
    """Entrada de `python -m devtools test-runner`: exit 0, 1 o 2 según el resultado."""
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
