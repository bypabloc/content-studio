"""Entrada de devtools: `python -m devtools <comando> [args]`.

Cada comando es un módulo con `main(argv) -> int` que se importa solo al pedirlo. Exit codes: 0 éxito, 1 validación
fallida u ocupado, 2 argumento inválido o error. stdout = resultado parseable (JSON); stderr = log humano.
"""

from __future__ import annotations

import importlib
import sys

COMANDOS = {
    'worktree': ('devtools.worktree', 'prepare | close: worktrees en ../content-studio-worktrees/'),
    'turno-gpu': ('devtools.turno_gpu', 'status | run: un modelo a la vez en la GPU entre sesiones'),
    'contexto-agentes': ('devtools.contexto_agentes', 'tamaño de lo que carga cada agente'),
    'reglas': ('devtools.reglas', '[--sincronizar]: .claude/ con el mismo cuerpo que .agents/'),
    'move-data': ('devtools.move_data', 'mueve narration/ y music/ a server/data/ (sin --apply, solo imprime el plan)'),
    'spelling': ('devtools.spelling', '[--staged] [archivo ...]: cspell sobre lo versionado o lo staged'),
}


def ayuda() -> str:
    filas = '\n'.join(f'  {n:<17} {d}' for n, (_, d) in COMANDOS.items())
    return f'uso: python -m devtools <comando> [args]\n\ncomandos:\n{filas}\n'


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ('-h', '--help'):
        sys.stderr.write(ayuda())
        return 0
    if argv[0] not in COMANDOS:
        sys.stderr.write(f'comando desconocido: {argv[0]}\n{ayuda()}')
        return 2
    modulo = importlib.import_module(COMANDOS[argv[0]][0])
    return modulo.main(argv[1:])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
