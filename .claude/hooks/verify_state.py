"""Stop: recuerda lo que fallaría el pre-commit o el pre-push antes de llegar ahí. No bloquea.

Con cambios sin confirmar: ruff de los .py cambiados, tests tdd efímeros vivos (tests/tdd/, el pre-push los
rechaza) y .py de src/ cambiados sin ningún test cambiado (TDD: test primero). Adaptado de klinikae.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', Path(__file__).resolve().parents[2]))


def changed(porcelain: str) -> list[str]:
    """Rutas de `git status --porcelain` (la de destino si es un rename).

    >>> changed(' M src/a.py\\n?? tests/test_a.py\\nR  b.py -> src/b.py\\n')
    ['src/a.py', 'tests/test_a.py', 'src/b.py']
    """
    return [line[3:].split(' -> ')[-1].strip('"') for line in porcelain.splitlines() if len(line) > 3]


def notes(files: list[str], ruff_out: str, tdd: list[str]) -> list[str]:
    """Avisos para el systemMessage.

    >>> notes(['src/a.py'], '', [])
    ['src/ cambió sin ningún test cambiado (TDD): src/a.py']
    >>> notes(['src/a.py', 'tests/test_a.py'], 'E501 ...', ['tests/tdd/test_x.py'])[0][:4]
    'ruff'
    """
    out: list[str] = []
    if ruff_out.strip():
        out.append('ruff: ' + ' | '.join(ruff_out.strip().splitlines()[:5]))
    if tdd:
        out.append('Tests tdd efímeros: bórralos o conviértelos en permanentes antes del push: ' + ', '.join(tdd))
    src = [f for f in files if f.startswith('src/') and f.endswith('.py')]
    if src and not any(f.startswith('tests/') for f in files):
        out.append('src/ cambió sin ningún test cambiado (TDD): ' + ', '.join(src[:5]))
    return out


def main() -> None:
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout
    files = [f for f in changed(status) if (ROOT / f).is_file()]
    if not files:
        return
    py = [f for f in files if f.endswith('.py')]
    ruff = ''
    if py:
        try:
            cmd = ['uv', 'run', 'ruff', 'check', '--quiet', '--output-format=concise', *py]
            ruff = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout
        except FileNotFoundError:
            ruff = ''
    tdd = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'tests/tdd').rglob('*.py')) if py else []
    found = notes(files, ruff, tdd)
    if found:
        print(json.dumps({'systemMessage': 'verify_state\n' + '\n'.join(found)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
