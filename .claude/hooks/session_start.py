"""SessionStart: `startup` revisa herramientas y rama; `compact` reinyecta las reglas críticas.

Lo impreso en stdout se agrega al contexto de la sesión. Nunca bloquea.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', Path(__file__).resolve().parents[2]))

RULES = """[Reglas críticas de content-studio reinyectadas]
- Código en server/src/content_studio/; server/data/narration/ y server/data/music/ son datos
  (no mover venvs ni modelos).
- Máximo 300 líneas por .py, Python 3.10.
- Dos capas: stdlib arriba; torch/numpy/motores dentro de funciones. Factory Method solo con 2+ productos.
- Un modelo a la vez en la GPU (8 GB). La música es siempre instrumental.
- Verificar antes de "listo": correr el script real; revisar duración, volumen y espectrograma (con image-reader).
- Antes de commit: uv run ruff check && uv run ruff format --check && uv run pytest.
- Ramas feature|fix|refactor|docs|test|chore|ci|perf|style|experiment|release/<kebab> desde dev; nunca push a main/dev.
- Conventional Commits en español, sin atribución de IA. Commit, push y merge solo cuando el usuario lo pida.
- GPU: todo lo que carga un modelo va con `python -m devtools gpu-turn run --job=<j> -- <cmd>`.
- Trabajo largo: handoff en tmp/handoff/<trabajo>/ (session-handoff.md); worktrees en ../content-studio-worktrees/.
- Specs en docs/specs/ con las plantillas de docs/specs/_plantilla/ (plan-format.md); estado en docs/process/."""


def check() -> str:
    notices = []
    missing = [h for h in ('uv', 'ffmpeg', 'nvidia-smi') if not shutil.which(h)]
    if missing:
        notices.append(f'Missing tools: {", ".join(missing)}.')
    if subprocess.run(['git', 'config', 'core.hooksPath'], cwd=ROOT, capture_output=True, text=True).stdout.strip() != (
        '.git-hooks'
    ):
        notices.append('Git hooks inactive: git config core.hooksPath .git-hooks')
    rama = subprocess.run(['git', 'branch', '--show-current'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if rama in {'main', 'dev'}:
        notices.append(f"Protected branch '{rama}': create a working branch from dev before committing.")
    return '[session_start] ' + (' '.join(notices) or f'Environment OK (branch {rama}).')


if __name__ == '__main__':
    print(RULES if sys.argv[1:] == ['compact'] else check())
