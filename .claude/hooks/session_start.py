"""SessionStart: `startup` revisa herramientas y rama; `compact` reinyecta las reglas críticas.

Lo impreso en stdout se agrega al contexto de la sesión. Nunca bloquea.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(os.environ.get('CLAUDE_PROJECT_DIR', Path(__file__).resolve().parents[2]))

REGLAS = """[Reglas críticas de content-studio reinyectadas]
- Código en src/content_studio/; narration/ y music/ son datos (no mover venvs ni modelos).
- Máximo 300 líneas por .py, Python 3.10.
- Dos capas: stdlib arriba; torch/numpy/motores dentro de funciones. Factory Method solo con 2+ productos.
- Un modelo a la vez en la GPU (8 GB). La música es siempre instrumental.
- Verificar antes de "listo": correr el script real; revisar duración, volumen y espectrograma (con image-reader).
- Antes de commit: uv run ruff check && uv run ruff format --check && uv run pytest.
- Ramas feature|fix|refactor|docs|test|chore|ci|perf|style|experiment|release/<kebab> desde dev; nunca push a main/dev.
- Conventional Commits en español, sin atribución de IA. Commit, push y merge solo cuando el usuario lo pida.
- GPU: todo lo que carga un modelo va con `python -m content_studio.devtools turno-gpu run --trabajo=<t> -- <cmd>`.
- Trabajo largo: handoff en tmp/handoff/<trabajo>/ (session-handoff.md); worktrees en ../content-studio-worktrees/.
- Specs en docs/specs/ con las plantillas de docs/specs/_plantilla/ (plan-format.md); estado en docs/process/."""


def chequeo() -> str:
    avisos = []
    faltan = [h for h in ('uv', 'ffmpeg', 'nvidia-smi') if not shutil.which(h)]
    if faltan:
        avisos.append(f'Faltan herramientas: {", ".join(faltan)}.')
    if subprocess.run(['git', 'config', 'core.hooksPath'], cwd=RAIZ, capture_output=True, text=True).stdout.strip() != (
        '.git-hooks'
    ):
        avisos.append('Git hooks inactivos: git config core.hooksPath .git-hooks')
    rama = subprocess.run(['git', 'branch', '--show-current'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    if rama in {'main', 'dev'}:
        avisos.append(f"Rama protegida '{rama}': crea una rama de trabajo desde dev antes de commitear.")
    return '[session_start] ' + (' '.join(avisos) or f'Entorno OK (rama {rama}).')


if __name__ == '__main__':
    print(REGLAS if sys.argv[1:] == ['compact'] else chequeo())
