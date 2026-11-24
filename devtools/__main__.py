"""Entrada de devtools: `python -m devtools <comando> [args]`.

Cada comando es un módulo con `main(argv) -> int` que se importa solo al pedirlo. Exit codes: 0 éxito, 1 validación
fallida u ocupado, 2 argumento inválido o error. stdout = resultado parseable (JSON); stderr = log humano.
"""

from __future__ import annotations

import importlib
import sys

COMMANDS = {
    'worktree': ('devtools.worktree', 'prepare | close: worktrees en ../content-studio-worktrees/'),
    'gpu-turn': ('devtools.gpu_turn', 'status | run: one model at a time on the GPU, across sessions'),
    'agent-context': ('devtools.agent_context', 'size of what each agent loads'),
    'rules': ('devtools.rules', '[--sync]: .claude/ with the same body as .agents/'),
    'move-data': (
        'devtools.move_data',
        'moves narration/ and music/ to server/data/ (without --apply, only prints the plan)',
    ),
    'spelling': ('devtools.spelling', '[--staged] [file ...]: cspell over the tracked or staged files'),
    'test-runner': ('devtools.test_runner.main', '--type=<stages> [--git-mode=...] [--files=...]: quality gates'),
    'app-check': ('devtools.app_check.main', 'run [--scenario=<n>] [--data=temp|real]: the real app over CDP'),
    'llm-eval': ('devtools.llm_eval', '[--models ...]: compare the assistant models in Spanish (needs the GPU)'),
}


def help() -> str:
    """Texto de ayuda con los comandos disponibles."""
    rows = '\n'.join(f'  {n:<17} {d}' for n, (_, d) in COMMANDS.items())
    return f'usage: python -m devtools <command> [args]\n\ncommands:\n{rows}\n'


def main(argv: list[str]) -> int:
    """Despacha `argv` al comando de devtools y devuelve su exit code."""
    if not argv or argv[0] in ('-h', '--help'):
        sys.stderr.write(help())
        return 0
    if argv[0] not in COMMANDS:
        sys.stderr.write(f'unknown command: {argv[0]}\n{help()}')
        return 2
    modulo = importlib.import_module(COMMANDS[argv[0]][0])
    return modulo.main(argv[1:])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
