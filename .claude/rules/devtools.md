# Devtools: flujo de trabajo de los agentes — SIEMPRE ACTIVA

`devtools/` (raíz) reúne las herramientas del flujo de trabajo (no del producto): worktrees, turno de la GPU y tamaño de las instrucciones. Python con solo stdlib, igual que el resto de `server/src/` (`codigo-python.md`). Lint y tests no pasan por aquí: son `uv run ruff` y `uv run pytest` (`testing.md`).

## 1. Invocación

```bash
python -m devtools --help           # desde la raíz; o uv run python -m ..., o PYTHONPATH=server/src python -m ...
python -m devtools <comando> [args]
```

| Comando | Qué hace |
| :--- | :--- |
| `worktree prepare <nombre>` | Enlaza venvs, motores, modelos y voces del principal, copia los audios de referencia, corre `bun install` y enlaza el target de Cargo al compartido (`worktrees.md`) |
| `worktree close <nombre>` | Cierra un worktree fusionado en `origin/dev`: enlaces, worktree y ramas |
| `gpu-turn status` | Quién tiene la GPU, VRAM en uso y sesiones abiertas del proyecto (exit 0 libre, 1 ocupada) |
| `gpu-turn run --job=<t> -- <cmd>` | Corre `<cmd>` con el turno tomado y lo suelta al terminar (`turno-gpu.md`) |
| `agent-context` | Mide lo que cargan Claude Code, Codex y Antigravity; exit 1 si algo pasa su límite. Lo corre el `pre-commit` |
| `app-check run [--scenario=<n>] [--data=temp\|real]` | Compila y abre la app del worktree aislada y corre escenarios de Playwright por CDP; capturas en `tmp/app-check/<run>/` (`verify-before-claiming-done.md` §3) |
| `llm-eval [--models ...]` | Corre los 50 casos en español de `tests/llm_eval/cases.jsonl` con cada modelo del asistente instalado (con el turno de la GPU) y deja `tmp/llm-eval/<fecha>/report.md` |
| `version <x.y.z>` · `version --check [--expect x.y.z]` | Escribe la versión de la app en los manifiestos y los locks, o falla si alguno difiere (el pre-commit lo corre en `validators`) |
| `bundle` | Arma los recursos del instalador en `client/src-tauri/bundle/`: `uv.exe` verificado, el server versionado con el lock y los datos que se siembran |
| `release --installer <exe> [--dry-run]` | Deja en `tmp/release/` el instalador, su firma, `latest.json` y las notas del Release; falla si pesa 60 MB o más (`docs/operations/release.md`) |
| `rules [--sync]` | Comprueba que cada regla y skill de `.claude/` tenga el mismo cuerpo que su fuente en `.agents/`; `--sync` reescribe las copias conservando el frontmatter de Claude (`agent-config-testing.md`) |

## 2. Estándar de un comando

* Un módulo `devtools/<comando>.py` con `main(argv: list[str]) -> int` y una línea en `COMMANDS` de `__main__.py` (se importa solo al pedirlo).
* Exit codes: `0` éxito, `1` validación fallida u ocupado, `2` argumento inválido o error.
* **stdout** = resultado parseable (JSON en una línea); **stderr** = log humano. Un comando usa otro importando su función, nunca por subprocess.
* Salidas en `tmp/<comando>/`; rutas desde la raíz del checkout (`paths.ROOT`) o del principal (`worktree.principal`), nunca desde el CWD.
* Tests unitarios en `devtools/tests/unit/test_<módulo>.py` (espejo de `devtools/<ruta>/<módulo>.py`); máximo 800 líneas por archivo de test.
* `test-runner` (specs 003 y 005): `python -m devtools test-runner --type=<etapas> [--git-mode=...] [--files=...]`. `ui-structure` (spec 008) mira `client/src/**/*.tsx` con el AST de TypeScript y no admite excepciones: `all` = `GROUPS['all']` de `devtools/test_runner/main.py`, sin `e2e` ni `tauri-check` (`WARNING/005-all-sin-e2e`). Cada etapa es una línea en `STAGES`.
* Nada de scripts sueltos fuera de `server/src/` (lo comprueba `tests/validators/test_structure.py`).
