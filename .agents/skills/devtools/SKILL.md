---
name: devtools
description: >
  Referencia de los devtools de content-studio (python -m devtools): worktree prepare|close,
  turno-gpu status|run, contexto-agentes y reglas. SIEMPRE invocar ANTES de crear o cerrar un worktree, de correr algo
  que cargue un modelo en la GPU, de editar reglas o skills de .agents/ o .claude/, o de escribir un comando nuevo en
  server/src/content_studio/devtools/. Usar cuando el usuario diga "devtools", "worktree", "turno de la GPU", "gpu ocupada",
  "sincronizar reglas", "contexto de agentes", "crear un comando de devtools".
allowed-tools: Read, Glob, Grep, Bash(python -m devtools:*), Bash(uv run python -m devtools:*)
argument-hint: "worktree | turno-gpu | contexto-agentes | reglas | crear <comando>"
---

# Devtools — content-studio

Fuente: `.agents/rules/devtools.md`. Desde la raíz del checkout (o con `uv run python -m …`).

| Necesitas | Comando |
| :--- | :--- |
| Worktree nuevo listo para correr motores | `git worktree add ../content-studio-worktrees/<n> -b <prefijo>/<n> origin/dev` y `python -m devtools worktree prepare <n>` |
| Cerrar tras el merge | `python -m devtools worktree close <n> [--handoff=<t>]` |
| Saber si la GPU está libre | `python -m devtools turno-gpu status` (exit 0 libre, 1 ocupada) |
| Correr algo que carga un modelo | `python -m devtools turno-gpu run --trabajo=<t> -- python cli.py music ...` |
| Medir lo que cargan los agentes | `python -m devtools contexto-agentes` |
| Copiar a `.claude/` una regla o skill editada en `.agents/` | `python -m devtools reglas --sincronizar` |

## Reglas

- Comandos nuevos: un módulo con `main(argv) -> int`, una línea en `COMANDOS`, test en `devtools/tests/test_devtools.py`.
- Exit 0/1/2; stdout JSON parseable, stderr humano; salidas en `tmp/<comando>/`.
- `worktree close` solo desde el checkout principal y con la rama ya fusionada en `origin/dev`.
- Las reglas y skills se editan en `.agents/` y se sincronizan; nunca solo la copia de `.claude/`.
