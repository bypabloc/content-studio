"""`test-runner`: corre las etapas de calidad (spec 003, D-1).

stdout = una línea JSON por etapa; stderr = resumen humano. Exit 0 si todas pasan, 1 si alguna falla, 2 con argumentos
inválidos. Lo llaman el pre-commit, el pre-push y la CI con `--type` y `--git-mode`.
"""

from __future__ import annotations

import json
import sys

from . import changeset, lint, validators
from .flags import parse

STAGES = {'lint': lint.run, 'validators': validators.run}


def main(argv: list[str]) -> int:
    try:
        options = parse(argv, list(STAGES))
    except ValueError as error:
        print(f'test-runner: {error}', file=sys.stderr)
        return 2
    picked = changeset.files(options.git_mode, options.files)
    if options.write_baseline:
        print(json.dumps({'baseline': validators.write_baseline(picked)}))
        return 0
    results = [STAGES[name](picked) for name in options.types]
    for result in results:
        print(json.dumps(result))
        print(f'{result["stage"]}: {result["status"]}', file=sys.stderr)
    return 1 if any(result['status'] == 'fail' for result in results) else 0
