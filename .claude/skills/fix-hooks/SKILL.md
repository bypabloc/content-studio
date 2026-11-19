---
name: fix-hooks
description: >
  Reproduce los gates de .git-hooks (pre-commit o pre-push) y repara cada error hasta que pasen. SIEMPRE invocar
  cuando un commit o un push es rechazado por un hook, o cuando el usuario pida arreglar ruff, pytest, estructura,
  sincronía de reglas, contexto de agentes o tests tdd antes del push. NUNCA saltar los hooks con --no-verify. Usar
  cuando el usuario diga "fix hooks", "arreglar hook", "pre-commit falla", "pre-push falla", "no me deja commitear",
  "no me deja pushear", "quality gates".
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(uv run ruff:*), Bash(uv run pytest:*), Bash(python -m devtools:*), Bash(git status:*), Bash(git diff:*)
argument-hint: "commit | push"
---

# Fix hooks — content-studio

Reproduce el gate, corrige y repite hasta exit 0. Qué corre cada hook: `.agents/rules/git-workflow.md`.

| Síntoma | Corrección |
| :--- | :--- |
| `La rama '…' no admite commits` | Crea una rama de trabajo desde `dev` con prefijo válido y mueve ahí los cambios |
| `Archivos que no se versionan` | `git restore --staged <archivo>`; nunca fuerces `out/`, `logs/`, `tmp/`, modelos, venvs ni audio |
| `ruff check` | `uv run ruff check --fix` y corrige a mano lo que quede (ANN001/ANN201: type hints en las firmas) |
| `ruff format --check` | `uv run ruff format` |
| `pytest` | Corre el test que falla solo (`uv run pytest <archivo>::<test> -q`), corrige el código; si el cambio de salida es intencional, regenera las fixtures en un commit aparte |
| `test_structure` (300 líneas, 3.10, sincronía) | Divide el archivo por responsabilidad; sintaxis 3.10; `python -m devtools rules --sync` tras editar `.agents/` |
| `agent-context` | Recorta la regla que pasa el límite y mueve el detalle a `docs/` |
| `pre-push`: tests tdd | Convierte `tests/tdd/*` en tests permanentes de su área o bórralos |
| `pre-push`: destino protegido o sin prefijo | Empuja una rama de trabajo y abre un PR |

## Reglas

- NUNCA `--no-verify` ni desactivar un chequeo para pasar el gate.
- Reporta "Iteración N: X errores" hasta el verde.
- Si un error exige una decisión de diseño que cambia el alcance, regístrala en `docs/process/WARNING/` (plugin `session-handoff`).
