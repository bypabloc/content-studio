# Spec 026: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `026-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-026/` o `tmp/spec-026/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run pytest -m local` | toca un motor o su registro |
| 4 | `python -m devtools test-runner --type=e2e` | toca el client |
| 5 | `python -m devtools agent-context` y `python -m devtools rules`, más la validación headless (`agent-config-testing.md`) | toca `.agents/`, `.claude/` o `AGENTS.md` |
| 6 | Por motor, con la carpeta aislada: `uv run studio narration tts …`, `uv run studio music …`, `uv run studio transcribe …` y `python -m devtools llm-eval --models <m>` (toman el candado solos) | siempre |
| 7 | Duración, LUFS y pico, y espectrograma en `tmp/spec-026/<motor>.png` revisado por `image-reader` | siempre |

## 2. Comprobaciones propias

1. Tabla en el PR: motor → Python, torch, paquete principal, commit/revisión, antes y después [AC-1, AC-2].
2. Cada salida de «debe sonar», medida contra la toma con la receta anterior [AC-4].
3. Con la base real en modo lectura (`app-check --data=real`), Motores muestra `outdated` en los instalados y no reinstala nada solo [AC-3, AC-7].

## 3. Escucha

Las rutas de `out/` de cada motor (antes y después) van en el PR. El agente elige con el «debe sonar» si una revisión nueva empeora y registra la elección.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Fichas de `docs/process/01-done/` actualizadas: `engines.md` (huella y «Actualizar»), `narration.md` y `music.md` (versiones de cada motor).
- [ ] Reglas y docs actualizadas: `stack.md` (tabla de motores y su Python), `codigo-python.md` (piso actual) y `AGENTS.md`; `python -m devtools rules --sync` y `python -m devtools agent-context`.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del README del lote en `DON`; la carpeta la borra la 033.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head chore/026-engines-python`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales), rutas de `out/` y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close 026-engines-python`.
