# Devtools: flujo de trabajo de los agentes — SIEMPRE ACTIVA

`server/src/content_studio/devtools/` reúne las herramientas del flujo de trabajo (no del producto): worktrees, turno de la GPU y tamaño de las instrucciones. Python con solo stdlib, igual que el resto de `server/src/` (`codigo-python.md`). Lint y tests no pasan por aquí: son `uv run ruff` y `uv run pytest` (`testing.md`).

## 1. Invocación

```bash
python -m devtools --help           # desde la raíz; o uv run python -m ..., o PYTHONPATH=server/src python -m ...
python -m devtools <comando> [args]
```

| Comando | Qué hace |
| :--- | :--- |
| `worktree prepare <nombre>` | Enlaza venvs, motores, modelos y voces del principal en un worktree nuevo y copia los audios de referencia (`worktrees.md`) |
| `worktree close <nombre>` | Cierra un worktree fusionado en `origin/dev`: enlaces, worktree y ramas |
| `gpu-turn status` | Quién tiene la GPU, VRAM en uso y sesiones abiertas del proyecto (exit 0 libre, 1 ocupada) |
| `gpu-turn run --job=<t> -- <cmd>` | Corre `<cmd>` con el turno tomado y lo suelta al terminar (`turno-gpu.md`) |
| `agent-context` | Mide lo que cargan Claude Code, Codex y Antigravity; exit 1 si algo pasa su límite. Lo corre el `pre-commit` |
| `rules [--sync]` | Comprueba que cada regla y skill de `.claude/` tenga el mismo cuerpo que su fuente en `.agents/`; `--sync` reescribe las copias conservando el frontmatter de Claude (`agent-config-testing.md`) |

## 2. Estándar de un comando

* Un módulo `server/src/content_studio/devtools/<comando>.py` con `main(argv: list[str]) -> int` y una línea en `COMANDOS` de `__main__.py` (se importa solo al pedirlo).
* Exit codes: `0` éxito, `1` validación fallida u ocupado, `2` argumento inválido o error.
* **stdout** = resultado parseable (JSON en una línea); **stderr** = log humano. Un comando usa otro importando su función, nunca por subprocess.
* Salidas en `tmp/<comando>/`; rutas desde la raíz del checkout (`paths.ROOT`) o del principal (`worktree.principal`), nunca desde el CWD.
* Tests unitarios en `devtools/tests/unit/test_<módulo>.py` (espejo de `devtools/<ruta>/<módulo>.py`); máximo 800 líneas por archivo de test.
* `test-runner` (spec 003): `python -m devtools test-runner --type=<etapas> [--git-mode=...] [--files=...]`. `all` = lint, spelling, validators, unit, typecheck y tdd; cada etapa es una línea en `STAGES` de `devtools/test_runner/main.py`.
* Nada de scripts sueltos fuera de `server/src/` (lo comprueba `tests/validators/test_structure.py`).
