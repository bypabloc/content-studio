---
trigger: always_on
description: devtools del flujo de agentes (worktree, turno-gpu, contexto-agentes) y el estándar para agregar un comando
---

# Devtools: flujo de trabajo de los agentes — SIEMPRE ACTIVA

`src/content_studio/devtools/` reúne las herramientas del flujo de trabajo (no del producto): worktrees, turno de la GPU y tamaño de las instrucciones. Python con solo stdlib, igual que el resto de `src/` (`codigo-python.md`). Lint y tests no pasan por aquí: son `uv run ruff` y `uv run pytest` (`testing.md`).

## 1. Invocación

```bash
python -m content_studio.devtools --help           # desde la raíz; o uv run python -m ..., o PYTHONPATH=src python -m ...
python -m content_studio.devtools <comando> [args]
```

| Comando | Qué hace |
| :--- | :--- |
| `worktree prepare <nombre>` | Enlaza venvs, motores, modelos y voces del principal en un worktree nuevo y copia los audios de referencia (`worktrees.md`) |
| `worktree close <nombre> [--handoff=<t>]` | Cierra un worktree fusionado en `origin/dev`: enlaces, worktree, ramas y handoff |
| `turno-gpu status` | Quién tiene la GPU, VRAM en uso y sesiones abiertas del proyecto (exit 0 libre, 1 ocupada) |
| `turno-gpu run --trabajo=<t> -- <cmd>` | Corre `<cmd>` con el turno tomado y lo suelta al terminar (`turno-gpu.md`) |
| `contexto-agentes` | Mide lo que cargan Claude Code, Codex y Antigravity; exit 1 si algo pasa su límite. Lo corre el `pre-commit` |
| `reglas [--sincronizar]` | Comprueba que cada regla y skill de `.claude/` tenga el mismo cuerpo que su fuente en `.agents/`; `--sincronizar` reescribe las copias conservando el frontmatter de Claude (`agent-config-testing.md`) |

## 2. Estándar de un comando

* Un módulo `src/content_studio/devtools/<comando>.py` con `main(argv: list[str]) -> int` y una línea en `COMANDOS` de `__main__.py` (se importa solo al pedirlo).
* Exit codes: `0` éxito, `1` validación fallida u ocupado, `2` argumento inválido o error.
* **stdout** = resultado parseable (JSON en una línea); **stderr** = log humano. Un comando usa otro importando su función, nunca por subprocess.
* Salidas en `tmp/<comando>/`; rutas desde la raíz del checkout (`rutas.RAIZ`) o del principal (`worktree.principal`), nunca desde el CWD.
* Tests en `tests/test_devtools.py`; máximo 300 líneas por archivo.
* Nada de scripts sueltos fuera de `src/` (lo comprueba `tests/test_estructura.py`).
