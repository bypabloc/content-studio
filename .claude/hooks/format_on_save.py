"""PostToolUse (Edit|Write): ruff format + ruff check --fix sobre el .py editado.

Solo server/src/, server/tests/, devtools/, tests/ y cli.py (lo que lintea CI). Nunca bloquea; si falta uv, lo avisa.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(os.environ.get('CLAUDE_PROJECT_DIR', Path(__file__).resolve().parents[2])).resolve()


def relativa(ruta: str) -> str | None:
    """Ruta posix relativa a la raíz si es un .py que CI lintea; None si no."""
    p = Path(ruta)
    p = (p if p.is_absolute() else RAIZ / p).resolve()
    try:
        rel = p.relative_to(RAIZ).as_posix()
    except ValueError:
        return None
    codigo = rel == 'cli.py' or rel.startswith(('server/src/', 'server/tests/', 'devtools/', 'tests/'))
    if p.suffix != '.py' or not codigo:
        return None
    return rel


def main() -> None:
    try:
        rel = relativa(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))
    except Exception:
        return
    if not rel:
        return
    try:
        for args in (['format'], ['check', '--fix', '--exit-zero', '--quiet']):
            subprocess.run(['uv', 'run', 'ruff', *args, rel], cwd=RAIZ, capture_output=True, check=False)
    except FileNotFoundError:
        print(json.dumps({'systemMessage': 'format_on_save: uv no está instalado'}))


if __name__ == '__main__':
    main()
